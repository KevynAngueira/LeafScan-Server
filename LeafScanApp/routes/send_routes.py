import os, json
from flask import Blueprint, request, jsonify, current_app
from core.paths import IMAGE_DIR, VIDEO_DIR, PARAMS_DIR
from core.cache import get_cache

from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference
from storage import get_meta_store, ARTIFACTS

send_bp = Blueprint("send", __name__)

@send_bp.route("/send/image", methods=["POST"])
def send_image():
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image file"}), 400
    image = request.files["image"]
    image_path = IMAGE_DIR / image.filename
    image.save(image_path)
    return jsonify({"status": "success", "filename": image.filename})

@send_bp.route("/send/video", methods=["POST"])
def send_video():
    if "video" not in request.files:
        return jsonify({"status": "error", "message": "No video file"}), 400
    
    video = request.files["video"]
    base = os.path.splitext(video.filename)[0]

    current_app.cache.save_video_stream(base, video)    
    current_app.cache.update(base, "simulated_area", {"video": video.filename})

    meta = get_meta_store()
    meta.update_field(base, ARTIFACTS["video"].input_flag)

    job, queue_size = schedule_simulated_inference(base, None)

    return jsonify({"status": "success", "filename": video.filename})

@send_bp.route("/send/params", methods=["POST"])
def send_params():
    data = request.get_json(force=True)
    filename = data.get("filename")
    params = data.get("params", {})

    if not filename or not params:
        return jsonify({"status": "error", "message": "Missing filename or params"}), 400

    base = os.path.splitext(filename)[0]
    current_app.cache.update(base, "simulated_area", params)
    current_app.cache.update(base, "original_area", params)

    cache = get_cache()
    cache.reset_entry(base)

    meta = get_meta_store()
    meta.update_field(base, ARTIFACTS["params"].input_flag)

    job, queue_size = schedule_original_inference(base, None)
    job, queue_size = schedule_simulated_inference(base, None)

    return jsonify({"status": "success", "filename": filename})
