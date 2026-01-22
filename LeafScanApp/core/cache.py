import time
import json
import requests
from datetime import datetime
from typing import Dict
from storage import ComputeCache, FileSystemComputeCache, get_meta_store, schedule_upload
from config.storage import CACHE_LOCATION

CACHE_SCHEMA = {
    "original_area": {
        "params": ["leafNumber", "leafWidths"],
        "results": ["original_area"]
    },
    "simulated_area": {
        "params": ["video", "length"],
        "results": ["simulated_area"]
    },
    "defoliation": {
        "params": ["original_area", "simulated_area"],
        "results": ["defoliation"]
    }
}

_cache = None

def get_cache():
    global _cache
    if _cache is None:
        backend = FileSystemComputeCache(CACHE_LOCATION)
        _cache = CacheService(backend)
    return _cache

class CacheService:
    """
    Cache logic + schema enforcement.
    Storage backend is injected.
    """

    def __init__(self, backend: ComputeCache):
        self.backend = backend
        self.meta = get_meta_store()

    def _artifact_name(self, entry_id: str, step: str) -> str:
        if step == "video":
            return f"{entry_id}_{step}.mp4"
        else:
            return f"{entry_id}_{step}.json"

    def reset(self):
        self.meta.reset()
        self.backend.clear()

    def load(self, entry_id: str, step: str) -> Dict:
        artifact = self._artifact_name(entry_id, step)

        if not self.backend.exists(artifact, entry_id=entry_id):
            return {"status": "waiting", "params": {}, "results": {}}

        raw = self.backend.get(artifact, entry_id=entry_id)
        return json.loads(raw.decode("utf-8"))

    def save(self, entry_id: str, step: str, cache: Dict):
        cache["last_updated"] = datetime.utcnow().isoformat() + "Z"
        artifact = self._artifact_name(entry_id, step)
        self.backend.put(artifact, json.dumps(cache, indent=2).encode("utf-8"), entry_id=entry_id)
        self.meta.update_bytes(entry_id)
        
        if cache.get("status") == "completed":
            local_path = self.backend._artifact_path(entry_id, artifact)
            schedule_upload(entry_id, artifact, local_path)

    def sanitize(self, step: str, cache: Dict) -> Dict:
        schema = CACHE_SCHEMA.get(step)
        if not schema:
            raise ValueError(f"Unknown cache type: {step}")

        cache["params"] = {
            k: cache.get("params", {}).get(k)
            for k in schema["params"]
        }
        cache["results"] = {
            k: cache.get("results", {}).get(k)
            for k in schema["results"]
        }
        return cache

    def update(self, entry_id: str, step: str, new_params: Dict = None) -> Dict:
        cache = self.load(entry_id, step)
        cache = self.sanitize(step, cache)

        schema_params = CACHE_SCHEMA[step]["params"]
        current_params = cache.get("params", {})

        new_params = new_params or {}
        updated = {
            k: new_params[k]
            for k in schema_params
            if k in new_params and current_params.get(k) != new_params[k]
        }

        if updated:
            cache["params"].update(updated)
            cache["results"] = {}

            if all(cache["params"].get(k) is not None for k in schema_params):
                cache["status"] = "ready"
            else:
                cache["status"] = "waiting"

            self.save(entry_id, step, cache)

        return cache

    def video_exists(self, entry_id: str) -> bool:
        artifact = self._artifact_name(entry_id, "video")
        return self.backend.exists(artifact, entry_id=entry_id)

    def load_video_stream(self, entry_id: str):
        artifact = self._artifact_name(entry_id, "video")
        return self.backend.get_stream(artifact, entry_id=entry_id)

    def save_video_stream(self, entry_id: str, file_storage):
        artifact = self._artifact_name(entry_id, "video")
        self.backend.put_stream(artifact, file_storage.stream, entry_id=entry_id)
        self.meta.update_bytes(entry_id)

        local_path = self.backend._artifact_path(entry_id, artifact)
        schedule_upload(entry_id, artifact, local_path)