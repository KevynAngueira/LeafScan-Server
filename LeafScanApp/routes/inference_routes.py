from flask import Blueprint, jsonify, current_app
from core.cache import CACHE_SCHEMA
from core.inputs import routes_to_rerun
from inference.all_schedulers import SCHEDULERS
from core.dependencies import check_dependencies
from inference.defoliation_schedule_inference import schedule_defoliation_inference
from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference
from storage import get_meta_store, JobFields

inference_bp = Blueprint("inference", __name__)

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
    meta = get_meta_store()
    result = meta.get_field(video_name, JobFields.RESULT_DEFOLIATION)
    try: 
        defoliation = float(result)
    except:
        defoliation = -1.0
    
    # 1️⃣ Return completed result immediately
    if defoliation != -1:
        meta.mark_results_fetched(video_name)
        return jsonify({
            "status": "completed",
            "message": "✅ Defoliation result ready",
            "results": {"defoliation": defoliation},
        })

    # 2️⃣ Otherwise, check for missing dependencies
    missing_params = []
    all_satisfied, jobs_to_reschedule = check_dependencies(video_name, JobFields.OUT_DEFOLIATION, missing_params)
    for r in jobs_to_reschedule:
        job, queue_size = SCHEDULERS[r](video_name, None)

    if all_satisfied:
        job, queue_size = schedule_defoliation_inference(video_name)
        return jsonify({
            "status": "queued",
            "message": f"📅 Defoliation job re-scheduled for {video_name}",
            "jobs_ahead": queue_size,
            "job_id": job.id,
        })
    else:
        routes = routes_to_rerun(missing_params)
        return jsonify({
            "status": "waiting",
            "message": "⚙️ Waiting for dependencies",
            "reupload": routes
        })
