from pathlib import Path
from .cache import ComputeCache


class FileSystemComputeCache(ComputeCache):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        # Safe key → filename mapping
        return self.base_dir / key.replace(":", "_")

    def put(self, key: str, data: bytes) -> None:
        path = self._path_for(key)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        path = self._path_for(key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._path_for(key).exists()

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        for file in self.base_dir.iterdir():
            if file.is_file():
                file.unlink()
