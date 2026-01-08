from flask import Blueprint, jsonify, current_app
from core.cache import load_cache, CACHE_SCHEMA
from core.inputs import routes_to_rerun
from inference.defoliation_schedule_inference import schedule_defoliation_inference
from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference

inference_bp = Blueprint("inference", __name__)

SCHEDULERS = {
    "original_area": schedule_original_inference,
    "simulated_area": schedule_simulated_inference,
    "defoliation": schedule_defoliation_inference
}

def check_dependencies(video_name, stage, missing_params):
    cache = load_cache(video_name, stage)
    current_params = cache['params']

    schema = CACHE_SCHEMA.get(stage, {})
    required_params = schema.get('params', [])

    no_missing = True
    for r in required_params: 
        if not current_params.get(r):
            if CACHE_SCHEMA.get(r, {}):
                sub_no_missing = check_dependencies(video_name, r, missing_params)
                
                if sub_no_missing:
                    job, queue_size = SCHEDULERS[r](video_name, None)

            else:
                missing_params.append(r)
                sub_no_missing = False

            no_missing = no_missing and sub_no_missing

    return no_missing

@inference_bp.route("/inference/<video_name>")
def inference_entry(video_name):
    """
    Unified inference endpoint:
    - Returns completed result if available.
    - Reschedules defoliation if ready.
    - Checks dependencies (original/simulated).
    - Reports missing first-level data dependencies for uploads.
    """
    #try:
    cache = load_cache(video_name, "defoliation")

    # 1️⃣ Return completed result immediately
    if cache and cache.get("status") == "completed":
        return jsonify({
            "status": "completed",
            "message": "✅ Defoliation result ready",
            "results": cache["results"],
        })

    # 2️⃣ If ready (parameters known, no result yet)
    if cache and cache.get("status") == "ready":
        job, queue_size = schedule_defoliation_inference(video_name, cache)
        return jsonify({
            "status": "queued",
            "message": f"📅 Defoliation job re-scheduled for {video_name}",
            "jobs_ahead": queue_size,
            "job_id": job.id,
        })

    # 3️⃣ Otherwise, check dependencies
    missing_params = []
    no_missing = check_dependencies(video_name, 'defoliation', missing_params)
    
    if not no_missing:
        routes = routes_to_rerun(missing_params)
        return jsonify({
            "status": "waiting",
            "message": "⚙️ Waiting for dependencies",
            "reupload": routes
        })
    else:
        job, queue_size = schedule_defoliation_inference(video_name, cache)
        return jsonify({
            "status": "queued",
            "message": f"📅 Defoliation job re-scheduled for {video_name}",
            "jobs_ahead": queue_size,
            "job_id": job.id,
        })

    #except Exception as e:
    #    return jsonify({
    #        "status": "error",
    #        "message": f"Inference dispatch failed: {e}",
    #    }), 500
