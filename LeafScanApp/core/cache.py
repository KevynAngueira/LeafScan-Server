import time
import json
import requests
from datetime import datetime
from typing import Dict
from storage import ComputeCache, FileSystemComputeCache, get_meta_store, schedule_upload, ARTIFACTS, JobFields, JobTypes
from core.dependencies import get_dependents
from config.storage import CACHE_LOCATION

CACHE_SCHEMA = {
    JobTypes.ORIGINAL_AREA: {
        "params": [JobFields.IN_LEAF, JobFields.IN_WIDTHS],
        "results": [JobFields.OUT_ORIGINAL]
    },
    JobTypes.SIMULATED_AREA: {
        "params": [JobFields.IN_VIDEO, JobFields.IN_LENGTH],
        "results": [JobFields.OUT_SIMULATED]
    },
    JobTypes.DEFOLIATION: {
        "params": [JobTypes.ORIGINAL_AREA, JobTypes.SIMULATED_AREA],
        "results": [JobFields.OUT_DEFOLIATION]
    }
}

FLAG_TO_JOB = {
    JobFields.OUT_ORIGINAL: JobTypes.ORIGINAL_AREA,
    JobFields.OUT_SIMULATED: JobTypes.SIMULATED_AREA,
    JobFields.OUT_DEFOLIATION: JobTypes.DEFOLIATION,
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

    def reset_entry(self, entry_id: str):
        for c in ["defoliation", "original_area", "simulated_area"]:
            state = self.load(entry_id, c)
            state["status"] = "waiting"
            state["results"] = {}
            self.save(entry_id, c, state)

        self.meta.reset_job(entry_id)

    def load(self, entry_id: str, step: str) -> Dict:
        artifact = self._artifact_name(entry_id, step)

        if not self.backend.exists(artifact, entry_id=entry_id):
            return {"status": "waiting", "params": {}, "results": {}}

        raw = self.backend.get(artifact, entry_id=entry_id)
        return json.loads(raw.decode("utf-8"))

    def save(self, entry_id: str, step: str, state: Dict):
        state["last_updated"] = datetime.utcnow().isoformat() + "Z"
        artifact = self._artifact_name(entry_id, step)
        self.backend.put(artifact, json.dumps(state, indent=2).encode("utf-8"), entry_id=entry_id)
        self.meta.update_bytes(entry_id)
    
        if state.get("status") == "completed":
            self.meta.update_field(entry_id, ARTIFACTS[step].upload_flag)
            local_path = self.backend._artifact_path(entry_id, artifact)
            schedule_upload(entry_id, step, local_path)

        self.meta.evict_jobs_for_space()

    def sanitize(self, step: str, state: Dict) -> Dict:
        schema = CACHE_SCHEMA.get(step)
        if not schema:
            raise ValueError(f"Unknown state type: {step}")

        state["params"] = {
            k: state.get("params", {}).get(k)
            for k in schema["params"]
        }
        state["results"] = {
            k: state.get("results", {}).get(k)
            for k in schema["results"]
        }
        return state

    def update(self, entry_id: str, step: str, new_params: Dict = None, new_data=False) -> Dict:
        
        # Load and Sanitize
        state = self.load(entry_id, step)
        state = self.sanitize(step, state)

        schema_params = CACHE_SCHEMA[step]["params"]
        current_params = state.get("params", {})
        new_params = new_params or {}

        # Capture which params have changed
        changed_params = {
            k: new_params[k]
            for k in schema_params
            if k in new_params and current_params.get(k) != new_params[k]
        }

        print(f"Input Params:{new_params} =====")
        print(f"Changed Params:{changed_params} =====")

        # Exit early if no changes
        if not changed_params:
            return

        # Update current entry
        self.meta.update_field(entry_id, ARTIFACTS[step].output_flag, 0)

        state["params"].update(changed_params)
        state["results"] = {}
        state["status"] = (
            "ready"
            if all(state["params"].get(k) is not None for k in schema_params)
            else "waiting"
        )    

        self.save(entry_id, step, state)

        # Update all dependents
        for param in changed_params.keys():
            param_field = param
            self.meta.update_field(entry_id, param_field, 1)
            
            for dep in get_dependents(entry_id, param_field):
                self.meta.update_field(entry_id, dep, 0)   

        print(f">>>> Update {entry_id} >>>>")
        print(self.meta.get_entry(entry_id))
        print(f"<<<< Update {entry_id} <<<<")
        print()

        return state

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
        self.meta.update_field(entry_id, ARTIFACTS["video"].upload_flag)
        schedule_upload(entry_id, "video", local_path)

        self.meta.evict_jobs_for_space()