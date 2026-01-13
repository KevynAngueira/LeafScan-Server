# core/storage/permanent.py

from abc import ABC, abstractmethod
from typing import Optional, Dict


class PermanentStore(ABC):
    """Durable, authoritative storage backend."""

    @abstractmethod
    def put(
        self,
        key: str,
        data: bytes,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
