from abc import ABC, abstractmethod

class ComputeCache(ABC):
    """Ephemeral, fast, node-local storage for compute."""

    @abstractmethod
    def put(self, artifact_name: str, data: bytes, entry_id: str | None = None) -> None:
        pass

    @abstractmethod
    def put_stream(self, artifact_name: str, stream, entry_id: str | None = None) -> None:
        pass

    @abstractmethod
    def get(self, artifact_name: str, entry_id: str | None = None) -> bytes:
        pass

    @abstractmethod
    def get_stream(self, artifact_name: str, entry_id: str | None = None):
        pass

    @abstractmethod
    def exists(self, artifact_name: str, entry_id: str | None = None) -> bool:
        pass

    @abstractmethod
    def delete(self, artifact_name: str | None = None, entry_id: str | None = None) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def compute_entry_size(self, entry_id: str) -> int:
        pass
