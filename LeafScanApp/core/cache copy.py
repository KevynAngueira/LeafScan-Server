import time
import json
import requests
from datetime import datetime
from typing import Dict
from storage import ComputeCache, FileSystemComputeCache
from storage.upload_tasks import schedule_upload
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

    def __init__(self, backend: ComputeCache, max_bytes: int = 1e10):
        self.backend = backend
        self.meta = CacheMetaStore(backend, max_bytes)

    def _artifact_name(self, entry_id: str, step: str) -> str:
        return f"{entry_id}_{step}.json"

    def reset(self):
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
        self.meta.update_entry(entry_id)
        
        if cache.get("status") == "completed":
            local_path = self.backend._artifact_path(entry_id, artifact)
            schedule_upload(artifact, local_path)

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
        artifact = f"{entry_id}.mp4"
        return self.backend.exists(artifact, entry_id=entry_id)

    def load_video_stream(self, entry_id: str):
        artifact = f"{entry_id}.mp4"
        return self.backend.get_stream(artifact, entry_id=entry_id)

    def save_video_stream(self, entry_id: str, file_storage):
        artifact = f"{entry_id}.mp4"
        self.backend.put_stream(artifact, file_storage.stream, entry_id=entry_id)
        self.meta.update_entry(entry_id)

        local_path = self.backend._artifact_path(entry_id, artifact)
        schedule_upload(artifact, local_path)


class CacheMetaStore:
    """
    Maintains cache metadata and enforces max_bytes limit.
    Persists metadata as a 'meta.json' artifact in the backend.
    """
    META_ARTIFACT = "meta.json"

    def __init__(self, backend: ComputeCache, max_bytes: int):
        self.backend = backend
        self.max_bytes = max_bytes
        self.meta = {
            "total_bytes": 0,
            "max_bytes": max_bytes,
            "entries": {}
        }
        self._load_meta()

    def _load_meta(self):
        if self.backend.exists(self.META_ARTIFACT, entry_id=None):
            try:
                raw = self.backend.get(self.META_ARTIFACT, entry_id=None)
                self.meta = json.loads(raw.decode("utf-8"))
            except Exception:
                # If corrupted, reset meta
                self.meta = {
                    "total_bytes": 0,
                    "max_bytes": self.max_bytes,
                    "entries": {}
                }
                self.backend.clear()

    def _save_meta(self):
        data = json.dumps(self.meta, indent=2).encode("utf-8")
        self.backend.put(self.META_ARTIFACT, data, entry_id=None)

    def update_entry(self, entry_id: str):
        now = time.time()
        bytes_used = self.backend.compute_entry_size(entry_id)
        entries = self.meta["entries"]

        if entry_id not in entries:
            entries[entry_id] = {
                "creation": now,
                "last_updated": now,
                "bytes": bytes_used
            }
        else:
            old_bytes = entries[entry_id]["bytes"]
            self.meta["total_bytes"] -= old_bytes
            entries[entry_id]["last_updated"] = now
            entries[entry_id]["bytes"] = bytes_used

        self.meta["total_bytes"] += bytes_used
        self.run_gc()
        self._save_meta()

    def run_gc(self):
        entries = self.meta["entries"]
        while self.meta["total_bytes"] > self.max_bytes and entries:
            # Evict the entry with the oldest last_updated timestamp
            evict_id = min(entries.items(), key=lambda e: e[1]["last_updated"])[0]
            self.backend.delete(entry_id=evict_id)
            self.meta["total_bytes"] -= entries[evict_id]["bytes"]
            del entries[evict_id]

    def get_meta(self):
        return self.meta