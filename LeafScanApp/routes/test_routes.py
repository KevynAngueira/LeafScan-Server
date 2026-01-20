import os, json
from flask import Blueprint, request, jsonify, current_app
from core.scheduler import inference_scheduler, upload_scheduler
from config.storage import DATA_STORE_URL
import requests

test_bp = Blueprint("test", __name__)

@test_bp.route('/test')
def test():
    response = {'status': 'success', 'message': 'Testing'}
    current_app.logger.info(f'{response}')
    return jsonify(response)

@test_bp.route('/reset', methods=["POST"])
def reset():
    try:
        # Stop and clear schedulers
        for sched in (inference_scheduler, upload_scheduler):
            try:
                sched.remove_all_jobs()
            except Exception:
                pass  # scheduler may already be stopped

        # Clear compute cache + metadata
        current_app.cache.reset()

        # 3. Call DataNode reset (testing only)
        try:
            r = requests.post(f"{DATA_STORE_URL}/reset", timeout=10)
            r.raise_for_status()
        except Exception as e:
            return jsonify({
                "status": "partial",
                "message": f"ComputeNode reset ok, DataNode reset failed: {e}"
            }), 207

        return jsonify({
            "status": "success",
            "message": "ComputeNode cache, schedulers, and DataNode storage reset"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to reset system: {e}"
        }), 500