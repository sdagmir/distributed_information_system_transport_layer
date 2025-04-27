from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class _MessageEntry:
    total: int
    segments: Dict[int, str] = field(default_factory=dict)


class InMemoryRepo:
    """
    Хранит сегменты сообщений в памяти, группируя по message_id.
    """

    def __init__(self):
        self._store: Dict[str, _MessageEntry] = {}

    async def save_segment(
        self,
        id: str,
        segment_index: int,
        total: int,
        payload: str,
    ) -> None:
        """
        Сохраняет один сегмент:
        - message_id — ключ всей серии сегментов
        - segment_index — номер сегмента (1..total)
        - total — общее число сегментов
        - payload — строка данных
        """
        entry = self._store.get(id)
        if entry is None:
            entry = _MessageEntry(total=total)
            self._store[id] = entry
        entry.segments[segment_index] = payload

    async def get_ready_messages(self) -> Dict[str, List[str]]:
        """
        Возвращает все сообщения, у которых уже получено `total` сегментов,
        в виде словаря `{ message_id: [payload1, payload2, ...] }`.
        """
        ready = {}
        for msg_id, entry in self._store.items():
            if len(entry.segments) == entry.total:
                ordered = [entry.segments[i]
                           for i in range(1, entry.total + 1)]
                ready[msg_id] = ordered
        return ready

    async def delete_message(self, id: str) -> None:
        """Удаляет полностью собранное сообщение из хранилища."""
        self._store.pop(id, None)
