import requests
import hashlib
import time
from pathlib import Path
from core.scheduler import upload_scheduler
from config.storage import DATA_STORE_URL

def schedule_upload(artifact: str, local_path: Path):
    job = upload_scheduler.add_job(
        func=upload_with_retry,
        args=[artifact, local_path, DATA_STORE_URL],
        id=f"upload_{artifact}",
        replace_existing=False
    )
    queue_size = len(upload_scheduler.get_jobs()) - 1
    print(f"Queued Upload Job -> {job.id}")
    return job, queue_size


def upload_with_retry(artifact: str, local_path: Path, data_node_url: str, max_attempts: int=10):
    upload_url = f"{data_node_url}/upload/{artifact}"
    exists_url = f"{data_node_url}/exists/{artifact}"

    for i in range(max_attempts):
        try:
            with open(local_path, "rb") as f:
                r = requests.post(upload_url, data=f, headers={"Content-Type": "application/octet-stream"}, timeout=120)
                r.raise_for_status()

            checksum = sha256(local_path)
            vr = requests.get(exists_url, params={"checksum": checksum}, timeout=30)
            vr.raise_for_status()

            if vr.json().get("exists") is True:
                print(f"✅ Upload verified: {artifact}")
                return True

        except Exception as e:
            print(f"⏳ Upload retry {artifact}: {e}")

        time.sleep(15)
    return False

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()
