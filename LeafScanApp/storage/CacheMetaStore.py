# storage/redis_meta_store.py

import time
import redis
import os

from .Cache import ComputeCache
from .FSCache import FileSystemComputeCache
from .JobSchema import JOB_SCHEMA
from config.storage import CACHE_LOCATION, CACHE_MAX_BYTES

_redis = None
_cache_meta_store = None

def get_meta_store():
    global _cache_meta_store
    if _cache_meta_store is None:
        backend = FileSystemComputeCache(CACHE_LOCATION)
        _cache_meta_store = CacheMetaStore(backend, CACHE_MAX_BYTES)
    return _cache_meta_store

def get_redis():
    global _redis
    if _redis is None:
        redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        _redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    return _redis

class CacheMetaStore:
    def __init__(self, backend: ComputeCache, max_bytes: int):
        self.r = get_redis()
        self.backend = backend
        self.max_bytes = int(max_bytes)

        # initialize global limits once
        self.r.setnx("cache:max_bytes", self.max_bytes)
        self.r.setnx("cache:total_bytes", 0)

    # ----------------------------
    # Job Management
    # ----------------------------

    def init_entry(self, entry_id: str):
        key = f"job:{entry_id}"
        if self.r.exists(key):
            return

        now = time.time()
        schema = JOB_SCHEMA.copy()
        schema["created_at"] = now
        schema["last_updated"] = now

        pipe = self.r.pipeline()
        pipe.hset(key, mapping=schema)
        pipe.zadd("cache:lru", {entry_id: now})
        pipe.zadd("cache:bytes", {entry_id: 0})
        pipe.execute()

    def ensure_exists(self, entry_id):
        key = f"job:{entry_id}"
        if not self.r.exists(key):
            self.init_entry(entry_id) 

    def get_field(self, entry_id: str, field: str):
        self.ensure_exists(entry_id)
        val = self.r.hget(f"job:{entry_id}", field)
        return val

    # ----------------------------
    # Update Tracking
    # ----------------------------

    def touch(self, entry_id: str):
        """Update last_updated timestamp and LRU score."""
        self.ensure_exists(entry_id)
        
        now = time.time()
        key = f"job:{entry_id}"
        pipe = self.r.pipeline()
        pipe.hset(key, mapping={
            "last_updated": now
        })
        pipe.zadd("cache:lru", {entry_id: now})
        pipe.execute()

    def update_field(self, entry_id: str, field: str, val=1):
        if field not in JOB_SCHEMA:
            raise ValueError(f"Unknown job field: {field}")

        self.ensure_exists(entry_id)
        self.r.hset(f"job:{entry_id}", field, val)
        self.touch(entry_id)

    def update_bytes(self, entry_id: str):
        """Recompute job size from backend, update total bytes, and touch entry."""
        self.ensure_exists(entry_id)
        key = f"job:{entry_id}"

        new_size_bytes = self.backend.compute_entry_size(entry_id)
        old_size = int(self.r.hget(key, "bytes") or 0)
        delta = new_size_bytes - old_size

        pipe = self.r.pipeline()
        pipe.hset(key, "bytes", new_size_bytes)
        pipe.zadd("cache:bytes", {entry_id: new_size_bytes})
        pipe.incrby("cache:total_bytes", delta)
        pipe.execute()

        self.touch(entry_id)
        self.run_gc()
   
    # ----------------------------
    # Eviction
    # ----------------------------

    def run_gc(self):
        max_bytes = int(self.r.get("cache:max_bytes"))
        total = self.get_total_bytes()

        while total > max_bytes:
            evicted = self._evict_one_safe_entry()
            if not evicted:
                raise RuntimeError(
                    "Cache full but no safe entries to evict (all jobs active or pending delivery)"
                )
            total = self.get_total_bytes()

    def _evict_one_safe_entry(self) -> bool:
        # Get LRU candidates
        candidates = self.r.zrange("cache:lru", 0, 10)

        for entry_id in candidates:
            job = self.r.hgetall(f"job:{entry_id}")

            # 1️⃣ unsafe if inference running or uploads pending
            inference_running = job.get("state") == "INFERENCING"
            uploads_pending = any(
                job.get(f"{field}") == "0"
                for field in [
                    "video_upload_done",
                    "original_area_upload_done",
                    "simulated_area_upload_done",
                    "defoliation_upload_done",
                ]
            )
            if inference_running or uploads_pending:
                continue  # cannot delete yet

            # 2️⃣ safe to delete intermediate files (keep final results)
            if job.get("results_fetched") == "0":
                self._delete_intermediate_files(entry_id)
                return True

            # 3️⃣ safe to delete full entry (results fetched)
            size_bytes = int(job.get("bytes", 0))
            self._delete_full_entry(entry_id, size_bytes)
            return True

        return False

    def _delete_intermediate_files(self, entry_id: str):
        self.backend.delete(entry_id=entry_id)

    def _delete_full_entry(self, entry_id: str, size_bytes: int):
        self.filesystem_backend.delete_all(entry_id)
        pipe = self.r.pipeline()
        pipe.delete(f"job:{entry_id}")
        pipe.zrem("cache:lru", entry_id)
        pipe.zrem("cache:bytes", entry_id)
        pipe.decrby("cache:total_bytes", size_bytes)
        pipe.execute()


    # ----------------------------
    # Query helpers
    # ----------------------------

    def get_entry(self, entry_id: str) -> dict:
        return self.r.hgetall(f"job:{entry_id}")
    
    def get_total_bytes(self) -> int:
        return int(self.r.get("cache:total_bytes") or 0)

    # ----------------------------
    # Cleanup
    # ----------------------------

    def reset(self):
        """
        Clears all LeafScan cache metadata from Redis.
        Safe to call in development.
        """
        pipe = self.r.pipeline()

        # delete all job hashes
        for key in self.r.scan_iter("job:*"):
            pipe.delete(key)

        # delete tracking sets and counters
        pipe.delete("cache:lru")
        pipe.delete("cache:bytes")

        # reinitialize limits
        pipe.set("cache:max_bytes", self.max_bytes)
        pipe.set("cache:total_bytes", 0)

        pipe.execute()

