from flask import Blueprint, jsonify, current_app
from core.cache import CACHE_SCHEMA
from core.inputs import routes_to_rerun
from core.dependencies import check_dependencies
from inference.defoliation_schedule_inference import schedule_defoliation_inference
from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference
from storage import get_meta_store, JobFields

inference_bp = Blueprint("inference", __name__)

'''
def check_dependencies(video_name, stage, missing_params):
    state = current_app.cache.load(video_name, stage)
    current_params = state['params']

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
'''

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
        return jsonify({
            "status": "completed",
            "message": "✅ Defoliation result ready",
            "results": {"defoliation": defoliation},
        })

    # 2️⃣ Otherwise, check for missing dependencies
    missing_params = []
    all_satisfied = check_dependencies(video_name, JobFields.OUT_DEFOLIATION, missing_params)

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
