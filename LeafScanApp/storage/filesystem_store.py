from pathlib import Path
from .permanent import PermanentStore
import json


class FileSystemPermanentStore(PermanentStore):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _data_path(self, key: str) -> Path:
        return self.base_dir / f"{key}.bin"

    def _meta_path(self, key: str) -> Path:
        return self.base_dir / f"{key}.meta.json"

    def put(self, key: str, data: bytes, metadata=None) -> None:
        data_path = self._data_path(key)
        data_path.write_bytes(data)

        if metadata:
            self._meta_path(key).write_text(json.dumps(metadata))

    def get(self, key: str) -> bytes:
        return self._data_path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._data_path(key).exists()
