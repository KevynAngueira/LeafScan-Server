# storage/redis_meta_store.py

import time
import redis
import os
import copy

from config.storage import CACHE_LOCATION, CACHE_MAX_BYTES

from .Cache import ComputeCache
from .FSCache import FileSystemComputeCache
from .JobSchema import JOB_SCHEMA, JobFields


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
        schema = copy.deepcopy(JOB_SCHEMA)
        schema["created_at"] = now
        schema["last_updated"] = now

        pipe = self.r.pipeline()
        pipe.hset(key, mapping=schema)
        pipe.zadd("cache:lru", {entry_id: now})
        pipe.zadd("cache:bytes", {entry_id: 0})
        pipe.zadd("cache:expired", {entry_id: now + (3600 * 24)})
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
            return

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
   
    # ----------------------------
    # Eviction
    # ----------------------------

    def finalize_job_if_complete(self, entry_id: str) -> bool:
        job = self.get_entry(entry_id)

        inference_complete = all(
            job.get(f"{field}") == "1"
            for field in [
                JobFields.OUT_ORIGINAL,
                JobFields.OUT_SIMULATED,
                JobFields.OUT_DEFOLIATION,
            ]
        )

        uploads_complete = all(
            job.get(f"{field}") == "1"
            for field in [
                JobFields.UP_VIDEO,
                JobFields.UP_ORIGINAL,
                JobFields.UP_SIMULATED,
                JobFields.UP_DEFOLIATION,
            ]
        )

        if not (inference_complete and uploads_complete):
            return False

        self.purge_job_artifacts(entry_id)

        return True

    def evict_expired_jobs_for_space(self):
        max_bytes = int(self.r.get("cache:max_bytes"))
        total = self.get_total_bytes()

        if total <= max_bytes:
            return

        now = time.time()

        expired = self.r.zrangebyscore("cache:expired", 0, now)

        for entry_id in expired:
            size_bytes = self.purge_job_artifacts(entry_id)
            self.purge_job_metadata(entry_id)
            total -= size_bytes
        
        if total <= max_bytes:
                return

        raise RuntimeError("Space Full - Try again later")

    def mark_results_fetched(self, entry_id: str):
        expire_at = time.time() + 3600  # 1 hour
        
        pipe = self.r.pipeline()
        pipe.hset(f"job:{entry_id}", JobFields.RESULT_FETCHED, "1")
        pipe.zadd("cache:expired", {entry_id: expire_at})
        pipe.execute()

    def purge_job_artifacts(self, entry_id: str):
        size_bytes = int(self.get_field(entry_id, JobFields.BYTES) or 0)
        if size_bytes == 0:
            return size_bytes

        self.backend.delete(entry_id=entry_id)

        pipe = self.r.pipeline()
        pipe.hset(f"job:{entry_id}", JobFields.BYTES, 0)
        pipe.decrby("cache:total_bytes", size_bytes)
        pipe.execute()
        
        return size_bytes

    def purge_job_metadata(self, entry_id: str):
        pipe = self.r.pipeline()
        pipe.delete(f"job:{entry_id}")
        pipe.zrem("cache:lru", entry_id)
        pipe.zrem("cache:expired", entry_id)
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
        pipe.delete("cache:expired")

        # reinitialize limits
        pipe.set("cache:max_bytes", self.max_bytes)
        pipe.set("cache:total_bytes", 0)

        pipe.execute()

    def reset_job(self, entry_id):    
        in_video = self.get_field(entry_id, JobFields.IN_VIDEO)
        in_params = self.get_field(entry_id, JobFields.IN_PARAMS)
        self.r.delete(f"job:{entry_id}")
        self.init_entry(entry_id)
        self.update_field(entry_id, JobFields.IN_VIDEO, in_video)
        self.update_field(entry_id, JobFields.IN_PARAMS, in_params)