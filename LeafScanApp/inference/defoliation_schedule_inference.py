from core.scheduler import scheduler
from .defoliation_inference import defoliation_inference

def schedule_defoliation_inference(video_name, state=None):
    job = scheduler.add_job(
        func=defoliation_inference,
        args=[video_name, state],
        id=f"defoliation_{video_name}",
        replace_existing=False
    )
    queue_size = len(scheduler.get_jobs()) - 1
    return job, queue_size
