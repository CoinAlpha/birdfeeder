import logging
from contextlib import closing
from typing import Dict, List, Optional

from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import NewTopic

log = logging.getLogger(__name__)


class KafkaTopicsManager:
    """Helper class to perform actions on kafka servers."""

    def __init__(self, bootstrap_servers: str):
        self._bootstrap_servers: str = bootstrap_servers

    def check_topic(self, topic: str) -> bool:
        return topic in self.list_topics()

    def create_topic(
        self, topic: str, partitions: int = 1, replication: int = 2, config: Optional[Dict] = None
    ) -> None:
        with closing(KafkaAdminClient(bootstrap_servers=self._bootstrap_servers)) as admin_client:
            admin_client.create_topics([NewTopic(topic, partitions, replication, topic_configs=config)])

    def delete_topic(self, topic: str) -> None:
        with closing(KafkaAdminClient(bootstrap_servers=self._bootstrap_servers)) as admin_client:
            admin_client.delete_topics([topic])

    def list_topics(self) -> List[str]:
        with closing(KafkaConsumer(bootstrap_servers=self._bootstrap_servers)) as consumer:
            return list(consumer.topics())
