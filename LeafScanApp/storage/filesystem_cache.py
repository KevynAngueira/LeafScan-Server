from pathlib import Path
import shutil
import uuid
import json
from .cache import ComputeCache

class FileSystemComputeCache(ComputeCache):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _entry_dir(self, entry_id: str | None) -> Path:
        if entry_id is None:
            return self.base_dir
        return self.base_dir / entry_id

    def _artifact_path(self, entry_id: str | None, artifact_name: str) -> Path:
        return self._entry_dir(entry_id) / artifact_name

    # =======================================
    #            PUT FUNCTIONS
    # =======================================

    def put(self, artifact_name: str, data: bytes, entry_id: str | None = None) -> None:
        entry_dir = self._entry_dir(entry_id)
        entry_dir.mkdir(parents=True, exist_ok=True)
        path = self._artifact_path(entry_id, artifact_name)

        tmp_path = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        tmp_path.write_bytes(data)
        tmp_path.replace(path)

    def put_json(self, artifact_name: str, obj: dict, entry_id: str | None = None) -> None:
        self.put(artifact_name, json.dumps(obj, indent=2).encode("utf-8"), entry_id=entry_id, atomic=True)

    def put_stream(self, artifact_name: str, stream, entry_id: str | None = None) -> None:
        entry_dir = self._entry_dir(entry_id)
        entry_dir.mkdir(parents=True, exist_ok=True)
        with open(self._artifact_path(entry_id, artifact_name), "wb") as f:
            shutil.copyfileobj(stream, f)

    def put_chunk(self, artifact_name: str, chunk: bytes, entry_id: str | None = None):
        path = self._artifact_path(entry_id, artifact_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "ab") as f:
            f.write(chunk)

    # =======================================
    #            GET FUNCTIONS
    # =======================================

    def get(self, artifact_name: str, entry_id: str | None = None) -> bytes:
        return self._artifact_path(entry_id, artifact_name).read_bytes()

    def get_json(self, artifact_name: str, entry_id: str | None = None) -> dict:
        raw = self.get(artifact_name, entry_id)
        return json.loads(raw.decode("utf-8"))

    def get_stream(self, artifact_name: str, entry_id: str | None = None):
        return open(self._artifact_path(entry_id, artifact_name), "rb")

    
    # =======================================
    #            HELPER FUNCTIONS
    # =======================================

    def exists(self, artifact_name: str, entry_id: str | None = None) -> bool:
        return self._artifact_path(entry_id, artifact_name).exists()

    def delete(self, artifact_name: str | None = None, entry_id: str | None = None):
        if artifact_name is None:
            # Delete entire entry folder
            if entry_id is None:
                raise ValueError("entry_id must be provided when deleting an entire entry folder")
            entry_dir = self._entry_dir(entry_id)
            if entry_dir.exists():
                shutil.rmtree(entry_dir, ignore_errors=True)
        else:
            # Delete a single artifact (either in entry folder or base dir)
            path = self._artifact_path(entry_id, artifact_name)
            if path.exists():
                path.unlink()

    def clear(self) -> None:
        for d in self.base_dir.iterdir():
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
            else:
                d.unlink()

    def compute_entry_size(self, entry_id: str) -> int:
        entry_dir = self._entry_dir(entry_id)
        if not entry_dir.exists():
            return 0
        return sum(f.stat().st_size for f in entry_dir.glob("*") if f.is_file())
