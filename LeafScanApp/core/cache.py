import json
from datetime import datetime
from typing import Dict
from storage import ComputeCache, FileSystemComputeCache

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
        _cache = CacheService(FileSystemComputeCache("/tmp/leafscan/cache"))
    return _cache

class CacheService:
    """
    Cache logic + schema enforcement.
    Storage backend is injected.
    """

    def __init__(self, backend: ComputeCache):
        self.backend = backend

    def _key(self, video_name: str, step: str) -> str:
        return f"{video_name}:{step}"

    def reset(self):
        self.backend.clear()

    def load(self, video_name: str, step: str) -> Dict:
        key = self._key(video_name, step)
        if not self.backend.exists(key):
            return {"status": "waiting", "params": {}, "results": {}}

        raw = self.backend.get(key)
        return json.loads(raw.decode("utf-8"))

    def save(self, video_name: str, step: str, cache: Dict):
        cache["last_updated"] = datetime.utcnow().isoformat() + "Z"
        key = self._key(video_name, step)
        self.backend.put(
            key,
            json.dumps(cache, indent=2).encode("utf-8")
        )

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

    def update(self, video_name: str, step: str, new_params: Dict = None) -> Dict:
        cache = self.load(video_name, step)
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

            self.save(video_name, step, cache)

        return cache
