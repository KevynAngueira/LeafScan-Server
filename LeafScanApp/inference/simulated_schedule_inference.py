from core.scheduler import inference_scheduler
from .simulated_inference import simulated_inference

def schedule_simulated_inference(video_name, state=None):
    job = inference_scheduler.add_job(
        func=simulated_inference,
        args=[video_name, state],
        id=f"simulated_{video_name}",
        replace_existing=False
    )
    queue_size = len(inference_scheduler.get_jobs()) - 1
    print(f"Queued Simulated Area Job -> {job.id}")
    return job, queue_size

