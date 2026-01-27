from core.scheduler import inference_scheduler
from .original_inference import original_inference

def schedule_original_inference(entry_id, state=None):
    job = inference_scheduler.add_job(
        func=original_inference,
        args=[entry_id, state],
        id=f"original_{entry_id}",
        replace_existing=False
    )
    queue_size = len(inference_scheduler.get_jobs()) - 1
    print(f"Queued Original Area Job -> {job.id}")
    return job, queue_size