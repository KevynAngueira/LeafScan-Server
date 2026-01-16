from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

inference_scheduler = BackgroundScheduler(
    jobstores={"default": MemoryJobStore()},
    executors={"default": ThreadPoolExecutor(5)},
    job_defaults={"coalesce": False, "max_instances": 1},
)
inference_scheduler.start()

upload_scheduler = BackgroundScheduler(
    jobstores={"default": MemoryJobStore()},
    executors={"default": ThreadPoolExecutor(8)},
    job_defaults={"coalesce": False, "max_instances": 1},
)
upload_scheduler.start()
