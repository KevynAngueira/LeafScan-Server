import os, json
from flask import Blueprint, request, jsonify, current_app

from core.cache import reset_cache

test_bp = Blueprint("test", __name__)

@test_bp.route('/test')
def test():
    response = {'status': 'success', 'message': 'Testing'}
    current_app.logger.info(f'{response}')
    return jsonify(response)

@test_bp.route('/reset')
def reset():
    try:
        reset_cache()  # clears all caches
        return jsonify({"status": "success", "message": "Server cache reset"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to reset cache: {e}"}), 500