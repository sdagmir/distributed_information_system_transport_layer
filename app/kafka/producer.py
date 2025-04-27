import json
from aiokafka import AIOKafkaProducer


class KafkaProducerWrapper:
    def __init__(self, brokers: list[str], topic: str):
        self._producer = AIOKafkaProducer(bootstrap_servers=brokers)
        self._topic = topic

    async def start(self):
        await self._producer.start()

    async def stop(self):
        await self._producer.stop()

    async def send_segment(self, id: str, segment: dict):
        await self._producer.send_and_wait(
            self._topic,
            json.dumps(segment, ensure_ascii=False).encode("utf-8"),
            key=id.encode("utf-8")
        )
