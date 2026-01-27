from flask import Blueprint, jsonify, current_app
from core.cache import CACHE_SCHEMA
from core.inputs import routes_to_rerun
from inference.all_schedulers import SCHEDULERS
from core.dependencies import check_dependencies, dependencies_ready
from inference.defoliation_schedule_inference import schedule_defoliation_inference
from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference
from storage import get_meta_store, JobFields

inference_bp = Blueprint("inference", __name__)

@inference_bp.route("/inference/<entry_id>")
def inference_entry(entry_id):
    """
    Unified inference endpoint:
    - Returns completed result if available.
    - Reschedules defoliation if ready.
    - Checks dependencies (original/simulated).
    - Reports missing first-level data dependencies for uploads.
    """
    #try:
    meta = get_meta_store()
    result = defoliation = float(meta.get_field(entry_id, JobFields.RESULT_DEFOLIATION) or -1.0)
    
    # 1️⃣ Return completed result immediately
    if meta.get_field(entry_id, JobFields.OUT_DEFOLIATION) and (defoliation != -1):
        meta.mark_results_fetched(entry_id)
        return jsonify({
            "status": "completed",
            "message": "✅ Defoliation result ready",
            "results": {"defoliation": defoliation},
        })

    # 2️⃣ Otherwise, check for missing dependencies
    ready, missing, rerunnable = dependencies_ready(entry_id, JobFields.OUT_DEFOLIATION)
    for r in rerunnable:
        job, queue_size = SCHEDULERS[r](entry_id, None)

    if ready:
        job, queue_size = schedule_defoliation_inference(entry_id)
        return jsonify({
            "status": "queued",
            "message": f"📅 Defoliation job re-scheduled for {entry_id}",
            "jobs_ahead": queue_size,
            "job_id": job.id,
        })
    else:
        routes = routes_to_rerun(missing)
        return jsonify({
            "status": "waiting",
            "message": "⚙️ Waiting for dependencies",
            "reupload": routes
        })
