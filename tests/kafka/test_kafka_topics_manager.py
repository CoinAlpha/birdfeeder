import pytest

from birdfeeder.kafka import KafkaTopicsManager


@pytest.fixture()
def topics_manager(kafka):
    return KafkaTopicsManager(f"localhost:{kafka.broker.service_port}")


def test_create_delete_topic(topics_manager: KafkaTopicsManager) -> None:

    topics_manager.create_topic("test", replication=1)
    assert topics_manager.check_topic("test")

    topics_manager.delete_topic("test")
    assert topics_manager.check_topic("test") is False
