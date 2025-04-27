import asyncio
from typing import Dict, List

import httpx
import json

from app.models.schemas import SendRequest, TransferRequest
from app.repos.inmemory import InMemoryRepo
from app.config import HTTPClientSettings


class MessageService:
    """
    Сервис для транспортного уровня:
    - "send": разбивает входящее сообщение на сегменты и отправляет на канальный уровень (code_url)
    - "transfer": принимает обратно декодированный сегмент и сохраняет его в репозиторий
    - "assembly": фоновая задача, которая раз в N секунд собирает полные сообщения и отправляет на прикладной уровень (receive_url)
    """

    def __init__(
        self,
        max_segment_size: int,
        assembly_period: str,
        repo: InMemoryRepo,
        http_client_cfg: HTTPClientSettings,
    ):
        self._max_size = max_segment_size
        if assembly_period.endswith("s"):
            self._period = int(assembly_period[:-1])
        else:
            self._period = int(assembly_period)

        self._repo = repo
        self._code_url = str(http_client_cfg.code_url)
        self._receive_url = str(http_client_cfg.receive_url)
        self._client = httpx.AsyncClient(timeout=None)

    async def add_message(self, req: SendRequest) -> None:
        """
        Разбивает полное сообщение на сегменты по max_segment_size
        и отправляет каждый сегмент в канал (code_url).
        message_id формируем как комбинацию time и sender.
        """
        message_id = f"{req.time}:{req.sender}"
        payload_bytes = req.payload.encode('utf-8')

        segments = []
        i = 0
        while i < len(payload_bytes):
            max_len = len(payload_bytes) - i
            for j in range(max_len, 0, -1):
                segment_try = payload_bytes[i:i+j]
                segment_str = segment_try.decode('utf-8', errors='ignore')

                body_try = {
                    "id": message_id,
                    "payload": segment_str,
                    "total": 0,
                    "number": 0,
                }
                body_json = json.dumps(
                    body_try, ensure_ascii=False).encode('utf-8')

                if len(body_json) <= self._max_size:
                    segments.append(segment_str)
                    i += len(segment_try)
                    break
            else:
                raise ValueError(
                    "Не удалось подобрать кусок payload в 150 байт.")

        total = len(segments)

        for idx, segment_str in enumerate(segments, start=1):
            body = {
                "id": message_id,
                "payload": segment_str,
                "total": total,
                "number": idx,
            }
            print(body)
            await self._client.post(self._code_url, json=body)

    async def transfer_segment(self, req: TransferRequest) -> None:
        """
        Принимает обратно сегмент из канального уровня и сохраняет в репозиторий.
        Предполагается, что запрос содержит:
        - time, payload, total, number
        - id внутри payload или его можно вычислить
        """
        await self._repo.save_segment(
            id=req.id,
            segment_index=req.number,
            total=req.total,
            payload=req.payload,
        )

    async def assemble_loop(self) -> None:
        """
        Фоновая задача: каждые self._period секунд проверяет репозиторий
        на полные сообщения, отправляет их на receive_url и очищает хранилище.
        """
        while True:
            ready: Dict[str, List[str]] = await self._repo.get_ready_messages()
            for msg_id, parts in ready.items():
                full_text = "".join(parts)
                payload = {
                    "time": int(msg_id.split(":")[0]),
                    "payload": full_text,
                }
                await self._client.post(self._receive_url, json=payload)
                await self._repo.delete_message(msg_id)
            await asyncio.sleep(self._period)

    def start_assembly(self) -> None:
        """
        Запуск фонового цикла (вызывать при старте приложения).
        """
        asyncio.create_task(self.assemble_loop())
