import json
from aiokafka import AIOKafkaConsumer
from app.models.schemas import TransferRequest


class KafkaConsumerWrapper:
    def __init__(self, brokers: list[str], topic: str, auto_offset_reset: str, service):
        self._consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=brokers,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            group_id="transport-layer-group"
        )
        self._service = service

    async def start(self):
        await self._consumer.start()

    async def stop(self):
        await self._consumer.stop()

    async def run(self):
        async for msg in self._consumer:
            data = json.loads(msg.value.decode("utf-8"))
            transfer_req = TransferRequest.parse_obj(data)
            await self._service.transfer_segment(transfer_req)
