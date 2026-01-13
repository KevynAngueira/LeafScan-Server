from core.scheduler import scheduler
from .original_inference import original_inference

def schedule_original_inference(video_name, state=None):
    job = scheduler.add_job(
        func=original_inference,
        args=[video_name, state],
        id=f"original_{video_name}",
        replace_existing=False
    )
    queue_size = len(scheduler.get_jobs()) - 1
    return job, queue_size