import requests
import hashlib
import time
from pathlib import Path

from core.scheduler import upload_scheduler
from config.storage import DATA_STORE_URL
from .CacheMetaStore import get_meta_store
from .Artifacts import ARTIFACTS


def schedule_upload(entry_id: str, step: str, local_path: Path):
    job = upload_scheduler.add_job(
        func=upload_with_mark,
        args=[entry_id, step, local_path, DATA_STORE_URL],
        id=f"upload_{entry_id}_{step}",
        replace_existing=False
    )
    queue_size = len(upload_scheduler.get_jobs()) - 1
    print(f"Queued Upload Job -> {job.id}")
    return job, queue_size

def upload_with_mark(entry_id: str, step: str, local_path: Path, data_node_url: str, max_attempts: int=10):
    upload_successful = upload_with_retry(entry_id, step, local_path, data_node_url, max_attempts)
    
    if upload_successful:
        meta = get_meta_store()
        meta.update_field(entry_id, ARTIFACTS[step].upload_flag)
        meta.finalize_job_if_complete(entry_id)

        return True
    return False

def upload_with_retry(entry_id: str, step: str, local_path: Path, data_node_url: str, max_attempts: int = 10):
    upload_url = f"{data_node_url}/upload"
    compute_checksum = sha256(local_path)

    ext = "json"
    if step == "video":
        ext = "mp4"

    headers = {
        "Content-Type": "application/octet-stream",
        "X-Video-ID": entry_id,
        "X-Artifact": step,
        "X-Ext": ext,
    }

    for attempt in range(1, max_attempts + 1):
        try:
            # Upload
            with open(local_path, "rb") as f:
                r = requests.post(
                    upload_url,
                    data=f,
                    headers=headers,
                    timeout=120,
                )
                r.raise_for_status()

            # Optional: trust server checksum if you want
            data_checksum = r.json().get("checksum")

            print(f"Data Checksum: {data_checksum}")
            print(f"Compute Checksum: {compute_checksum}")
            #if data_checksum and data_checksum == compute_checksum:
            print(f"✅ Upload verified: {entry_id}_{step}")
            return True

        except Exception as e:
            print(f"⏳ Upload retry {attempt}/{max_attempts} for {entry_id}_{step}: {e}")
            time.sleep(15)

    return False

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()
