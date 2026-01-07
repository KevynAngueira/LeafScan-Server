from core.scheduler import scheduler
from .simulated_inference import simulated_inference

def schedule_simulated_inference(video_name, cache):
    job = scheduler.add_job(
        func=simulated_inference,
        args=[video_name, cache],
        id=f"simulated_{video_name}",
        replace_existing=False
    )
    queue_size = len(scheduler.get_jobs()) - 1
    return job, queue_size

