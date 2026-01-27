from core.scheduler import inference_scheduler
from .defoliation_inference import defoliation_inference

def schedule_defoliation_inference(entry_id, state=None):
    job = inference_scheduler.add_job(
        func=defoliation_inference,
        args=[entry_id, state],
        id=f"defoliation_{entry_id}",
        replace_existing=False
    )
    queue_size = len(inference_scheduler.get_jobs()) - 1
    print(f"Queued Defoliation Job -> {job.id}")
    return job, queue_size
