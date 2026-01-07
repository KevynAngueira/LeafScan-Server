import os
from flask import Blueprint, jsonify
from core.cache import load_cache
from core.paths import VIDEO_DIR
from core.scheduler import scheduler

from inference.defoliation_schedule_inference import schedule_defoliation_inference
from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference

inference_bp = Blueprint("inference", __name__)

@inference_bp.route("/inference/simulated/<video_name>")
def inference_simulated(video_name):
    
    job, queue_size = schedule_simulated_inference(video_name)

    return jsonify({
        "status": 'queued',
        "message": f"Job scheduled for {video_name}",
        "jobs_ahead": queue_size,
        "job_id": job.id
    })


@inference_bp.route("/inference/original/<video_name>")
def inference_original(video_name):

    job, queue_size = schedule_original_inference(video_name)

    return jsonify({
        "status": 'queued',
        "message": f"Job scheduled for {video_name}",
        "jobs_ahead": queue_size,
        "job_id": job.id
    })
    
@inference_bp.route("/inference/defoliation/<video_name>")
def inference_defoliation(video_name):
    
    job, queue_size = schedule_defoliation_inference(video_name)

    return jsonify({
        "status": 'queued',
        "message": f"Job scheduled for {video_name}",
        "jobs_ahead": queue_size,
        "job_id": job.id
    })
    
    