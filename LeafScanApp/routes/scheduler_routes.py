import os, json
from flask import Blueprint, request, jsonify

from core.scheduler import scheduler

scheduler_bp = Blueprint("scheduler", __name__)

@scheduler_bp.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    job = scheduler.get_job(job_id)
    if not job:
        return jsonify({"status": "completed or not found"})

    next_run = job.next_run_time.isoformat() if job.next_run_time else None
    return jsonify({
        "job_id": job_id,
        "next_run_time": next_run,
        "pending_jobs": len(scheduler.get_jobs())
    })
