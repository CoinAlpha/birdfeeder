import logging
import os
import shutil
import socket
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Any, Callable, ContextManager, Generator, NamedTuple

import docker
import pytest
import sqlalchemy
from kafka import KafkaConsumer
from kafka.errors import UnrecognizedBrokerVersion
from redis.sentinel import MasterNotFoundError, Sentinel
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import close_all_sessions
from sqlalchemy_utils import create_database, database_exists, drop_database

from birdfeeder.kafka import KafkaTopicsManager

log = logging.getLogger(__name__)


class KafkaCluster(NamedTuple):
    zookeeper: Any
    broker: Any
    bootstrap_servers: str


@pytest.fixture(scope="session")
def session_id() -> str:
    """
    Generate unique session id.

    This is needed in case testsuite may run in parallel on the same server, for example if CI/CD is being used. CI/CD
    infrastructure may run tests for each commit, so these tests should not influence each other.
    """
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def unused_port():
    """Obtain unused port to bind some service."""

    def _unused_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    return _unused_port


@pytest.fixture(scope="session")
def docker_manager():
    """Initialize docker management client."""
    return docker.from_env(version="auto")


@pytest.fixture(scope="session")
def kafka_cluster(session_id, unused_port, docker_manager):
    """Run kafka cluster in docker containers."""
    network = docker_manager.networks.create(f"kafka-test-{session_id}")

    zk_port = unused_port()
    zookeeper = docker_manager.containers.run(
        image="wurstmeister/zookeeper:latest",
        name=f"zookeeper-{session_id}",
        network=network.name,
        ports={"2181": zk_port},
        environment={"ZOOKEEPER_CLIENT_PORT": 2181},
        detach=True,
    )

    broker_port = unused_port()
    broker = docker_manager.containers.run(
        image="wurstmeister/kafka:2.12-2.2.2",
        name="broker-{}".format(session_id),
        network=network.name,
        ports={broker_port: broker_port},
        environment={
            "KAFKA_BROKER_ID": 0,
            "KAFKA_ZOOKEEPER_CONNECT": f"zookeeper-{session_id}:2181",
            "KAFKA_ADVERTISED_LISTENERS": f"INSIDE://127.0.0.1:9092,OUTSIDE://127.0.0.1:{broker_port}",
            "KAFKA_LISTENERS": f"INSIDE://:9092,OUTSIDE://:{broker_port}",
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT",
            "KAFKA_INTER_BROKER_LISTENER_NAME": "INSIDE",
            "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
            "KAFKA_MESSAGE_MAX_BYTES": 104857600,
        },
        detach=True,
    )
    zookeeper.service_port = zk_port
    broker.service_port = broker_port
    yield KafkaCluster(zookeeper=zookeeper, broker=broker, bootstrap_servers=f"127.0.0.1:{broker.service_port}")

    # Cleanup everything after test run
    zookeeper.remove(v=True, force=True)
    broker.remove(v=True, force=True)
    network.remove()


def wait_kafka(kafka_cluster: KafkaCluster, retries: int = 60) -> None:
    """Waits for kafka cluster to be ready."""
    while retries:
        try:
            with socket.create_connection(("127.0.0.1", kafka_cluster.broker.service_port), timeout=5):
                consumer = KafkaConsumer(bootstrap_servers=kafka_cluster.bootstrap_servers)
                consumer.close()
                break
        except (
            OSError,
            ValueError,
            UnrecognizedBrokerVersion,
        ):
            if not retries:
                raise
            retries -= 1
            log.debug(f"Kafka retries left: {retries}")
            time.sleep(1)


@pytest.fixture()
def kafka(kafka_cluster: KafkaCluster, caplog: pytest.LogCaptureFixture) -> Generator[KafkaCluster, None, None]:
    """Helper fixture to cleanup kafka topic after each test."""
    caplog.set_level(logging.WARNING, "kafka")
    caplog.set_level(logging.WARNING, "aiokafka")
    wait_kafka(kafka_cluster)
    manager = KafkaTopicsManager(kafka_cluster.bootstrap_servers)
    yield kafka_cluster

    topics = manager.list_topics()
    for topic in topics:
        manager.delete_topic(topic)


@pytest.fixture(scope="session")
def mysql(session_id, unused_port, docker_manager):
    """Creates MySQL docker container."""
    port = unused_port()
    password = "pass"
    volume = f"/tmp/mysql-data/{session_id}" if os.getenv("CI") else f"birdfeeder-mysql-test-{session_id}"
    options = " ".join(
        [
            "--innodb-flush-log-at-trx-commit=0",
            "--skip-innodb-doublewrite",
            "--innodb-flush-method=O_DIRECT_NO_FSYNC",
            "--innodb-file-per-table=OFF",
            "--sql-mode=''",
        ]
    )

    container = docker_manager.containers.run(
        image="mysql:5.7",
        # Setting some command-line options to speed up test execution and to bring AWS settings
        command=options,
        name=f"mysql-{session_id}",
        ports={"3306": port},
        environment={"MYSQL_ROOT_PASSWORD": password},
        # Speed up MySQL startup time, approx 30 seconds
        volumes=[f"{volume}:/var/lib/mysql:rw"],
        detach=True,
        # needed for compatibility with Apple Silicon computers
        # becausre there's no ARM version of MySQL 5.7 image
        platform="linux/x86_64",
    )
    container.service_port = port
    container.user = "root"
    container.host = "127.0.0.1"
    container.password = password

    try:
        yield container
    finally:
        # Cleanup everything after test run
        container.remove(v=True, force=True)


def wait_db(url: str, retries: int = 60) -> None:
    """Waits for server readiness."""
    while retries:
        try:
            database_exists(url)
            return
        except sqlalchemy.exc.OperationalError:
            if not retries:
                raise
            retries -= 1
            log.debug(f"MySQL retries left: {retries}")
            time.sleep(1)


@pytest.fixture(scope="session")
def get_new_db() -> Callable[[docker.models.containers.Container, str], ContextManager[URL]]:
    @contextmanager
    def _get_new_db(mysql: docker.models.containers.Container, session_id: str) -> Generator[URL, None, None]:
        db_name = f"parrot-{session_id}"
        db_url = URL.create(
            "mysql+mysqldb",
            username=mysql.user,
            password=mysql.password,
            host=mysql.host,
            port=mysql.service_port,
            database=db_name,
        )

        wait_db(db_url)
        create_database(db_url)
        try:
            yield db_url
        finally:
            # if a test case leave some SQL Sessions open at this point
            # then the database will keep locks for them
            # and "DROP" operation below will freeze current run of test suite
            # so we should close all active sessions manually
            # keep in mind that your tests shouldn't create locks for shared resources
            close_all_sessions()
            drop_database(db_url)

    return _get_new_db


@pytest.fixture(scope="class")
def redis_sentinel_config_template_path():
    """
    Provides python-style template for redis sentinel config, as a path.

    Override this fixture in your project
    """
    here = Path(__file__).parent
    path = PurePath(here).joinpath(".", "sample_configs", "redis_sentinel_config")
    return path


@pytest.fixture(scope="class")
def redis_cluster(session_id, unused_port, docker_manager, redis_sentinel_config_template_path):

    volume = f"/tmp/redis_config_{session_id}"
    Path(volume).mkdir(exist_ok=True)

    network = docker_manager.networks.create(f"redis-test-{session_id}")

    master_host = f"redis-master-{session_id}"
    master_port = unused_port()

    slave_host = f"redis-slave-{session_id}"
    slave_port = unused_port()

    sentinel_host = f"redis-sentinel-{session_id}"
    sentinel_port = unused_port()

    with open(redis_sentinel_config_template_path) as fd:
        rendered_config = fd.read().format(**vars())
        with open(Path(volume) / "sentinel", "w") as target:
            target.write(rendered_config)

    master = docker_manager.containers.run(
        image="redis:6.2.6",
        name=master_host,
        network_mode="host",
        detach=True,
        command=f"redis-server --port {master_port}",
    )

    slave = docker_manager.containers.run(
        image="redis:6.2.6",
        name=slave_host,
        network_mode="host",
        detach=True,
        command=f"redis-server --port {slave_port} --replicaof localhost {master_port}",
    )

    sentinel = docker_manager.containers.run(
        image="redis:6.2.6",
        name=sentinel_host,
        network_mode="host",
        detach=True,
        volumes=[f"{volume}:/redis_configs:rw"],
        command=(
            'bash -c "chown redis:redis /redis_configs/sentinel ' '&& redis-server /redis_configs/sentinel --sentinel"'
        ),
    )

    # wait up to 5 seconds for master to be ready
    try:

        for _ in range(5):
            client = Sentinel([("localhost", sentinel_port)])
            master_conn = client.master_for("mymaster")
            try:
                if master_conn.ping():
                    break
            except MasterNotFoundError:
                time.sleep(1)
                continue
        else:
            pytest.fail("Timeout waiting for initialization of redis master fixture")

        yield "localhost", sentinel_port

    finally:
        master.remove(v=True, force=True)
        slave.remove(v=True, force=True)
        sentinel.remove(v=True, force=True)
        network.remove()

        shutil.rmtree(volume)
