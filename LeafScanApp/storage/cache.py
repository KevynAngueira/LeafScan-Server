
from abc import ABC, abstractmethod


class ComputeCache(ABC):
    """Ephemeral, fast, node-local storage for compute."""

    @abstractmethod
    def put(self, key: str, data: bytes) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear entire cache (best-effort)."""
        pass
