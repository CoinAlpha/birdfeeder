pytest_plugins = ["birdfeeder.pytest_fixtures"]


def test_session_id(session_id):
    assert session_id is not None


def test_unused_port(unused_port):
    port = unused_port()
    assert 0 < port < 65536


def test_kafka(kafka):
    assert kafka.broker is not None
    assert kafka.zookeeper is not None
    assert kafka.bootstrap_servers is not None


def test_get_new_db(get_new_db, mysql, session_id):
    with get_new_db(mysql, session_id) as db_url:
        assert db_url is not None


def test_redis_cluster(redis_cluster):
    host, port = redis_cluster
    assert host is not None
    assert port is not None
