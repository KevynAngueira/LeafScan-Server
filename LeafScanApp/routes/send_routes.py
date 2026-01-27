import os, json, time
from flask import Blueprint, request, jsonify, current_app
from core.paths import IMAGE_DIR, VIDEO_DIR, PARAMS_DIR

from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference
from storage import ARTIFACTS, JobFields, JobTypes

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
    if JobTypes.VIDEO not in request.files:
        return jsonify({"status": "error", "message": "No video file"}), 400
    
    video = request.files["video"]
    base = os.path.splitext(video.filename)[0]

    current_app.cache.save_video_stream(base, video)    
    current_app.cache.update(base, JobTypes.SIMULATED_AREA, {JobFields.IN_VIDEO: video.filename}, new_data=True)

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

    print(f"\nParams:\n{params}\n")
    
    current_app.cache.update(base, JobTypes.ORIGINAL_AREA, params, new_data=True)
    current_app.cache.update(base, JobTypes.SIMULATED_AREA, params, new_data=True)

    job, queue_size = schedule_original_inference(base, None)
    job, queue_size = schedule_simulated_inference(base, None)

    return jsonify({"status": "success", "filename": filename})
