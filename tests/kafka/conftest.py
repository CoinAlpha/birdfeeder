import socket
import time
import uuid
from typing import Any, NamedTuple

import docker
import pytest
from kafka import KafkaConsumer


class Cluster(NamedTuple):
    zookeeper: Any
    broker: Any


@pytest.fixture(scope="session")
def session_id():
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
        image="confluentinc/cp-zookeeper:5.5.0",
        name=f"zookeeper-{session_id}",
        network=network.name,
        ports={"2181": zk_port},
        environment={"ZOOKEEPER_CLIENT_PORT": 2181},
        detach=True,
    )

    broker_port = unused_port()
    broker = docker_manager.containers.run(
        image="confluentinc/cp-kafka:5.5.0",
        name="broker-{}".format(session_id),
        network=network.name,
        ports={broker_port: broker_port},
        environment={
            "KAFKA_BROKER_ID": 0,
            "KAFKA_ZOOKEEPER_CONNECT": f"zookeeper-{session_id}:2181",
            "KAFKA_ADVERTISED_LISTENERS": (
                f"PLAINTEXT://localhost:9092,CONNECTIONS_FROM_HOST://localhost:{broker_port}"
            ),
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,CONNECTIONS_FROM_HOST:PLAINTEXT",
            "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
        },
        detach=True,
    )
    zookeeper.service_port = zk_port
    broker.service_port = broker_port
    yield Cluster(zookeeper=zookeeper, broker=broker)

    # Cleanup everything after test run
    zookeeper.remove(v=True, force=True)
    broker.remove(v=True, force=True)
    network.remove()


@pytest.fixture(scope="session")
def kafka(kafka_cluster):
    """Waits for kafka cluster to be ready."""
    while True:
        try:
            with socket.create_connection(("localhost", kafka_cluster.broker.service_port), timeout=5):
                KafkaConsumer(bootstrap_servers=f"localhost:{kafka_cluster.broker.service_port}")
                break
        except (OSError, ValueError):
            time.sleep(1)

    return kafka_cluster
