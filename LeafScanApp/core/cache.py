import json, os
import shutil
from datetime import datetime

CACHE_DIR = "cache"
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

def reset_cache():
    shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_dir(video_name: str):
    path = os.path.join(CACHE_DIR, video_name)
    os.makedirs(path, exist_ok=True)
    return path

def load_cache(video_name: str, step: str):
    path = os.path.join(get_cache_dir(video_name), f"{step}.json")
    if not os.path.exists(path):
        return {"status": "waiting", "params": {}, "results": {}}
    with open(path, "r") as f:
        return json.load(f)

def save_cache(video_name: str, step: str, cache: dict):
    cache["last_updated"] = datetime.utcnow().isoformat() + "Z"
    path = os.path.join(get_cache_dir(video_name), f"{step}.json")
    with open(path, "w") as f:
        json.dump(cache, f, indent=2)

def sanitize_cache(cache_type: str, cache: dict):
    schema = CACHE_SCHEMA.get(cache_type)
    if not schema:
        raise ValueError(f"Unknown cache type: {cache_type}")

    params = {k: cache.get("params", {}).get(k) for k in schema["params"]}
    results = {k: cache.get("results", {}).get(k) for k in schema["results"]}

    cache["params"] = params
    cache["results"] = results
    return cache

def update_cache(video_name: str, step: str, new_params: dict = None):
    """
    Loads a cache, updates params if provided, and sets status accordingly.
    Returns the updated cache dictionary.
    """
    cache = load_cache(video_name, step)
    cache = sanitize_cache(step, cache)

    schema_params = CACHE_SCHEMA[step]['params']
    current_params = cache.get('params', {})

    new_filtered_params = {k: new_params[k] for k in schema_params if k in (new_params or {})}
    new_updated_params = {k: v for k, v in new_filtered_params.items() if current_params.get(k) != v}

    if new_updated_params:
        cache['params'].update(new_updated_params)
        cache['results'] = {}

        all_params_present = all(cache['params'].get(k) is not None for k in schema_params)

        if not all_params_present:
            cache['status'] = 'waiting'
        else:
            cache['status'] = 'ready'

        save_cache(video_name, step, cache)

    return cache
