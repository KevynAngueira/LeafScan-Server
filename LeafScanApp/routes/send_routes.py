import os, json
from flask import Blueprint, request, jsonify, current_app
from core.cache import update_cache
from core.paths import IMAGE_DIR, VIDEO_DIR, PARAMS_DIR

from inference.original_schedule_inference import schedule_original_inference
from inference.simulated_schedule_inference import schedule_simulated_inference

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
    video_path = VIDEO_DIR / video.filename
    video.save(video_path)

    base = os.path.splitext(video.filename)[0]
    update_cache(base, "simulated_area", {"video": video.filename})

    job, queue_size = schedule_simulated_inference(base, None)
    print(job.id)

    return jsonify({"status": "success", "filename": video.filename})

@send_bp.route("/send/params", methods=["POST"])
def send_params():
    data = request.get_json(force=True)
    filename = data.get("filename")
    params = data.get("params", {})

    if not filename or not params:
        return jsonify({"status": "error", "message": "Missing filename or params"}), 400

    with open(PARAMS_DIR / (os.path.splitext(filename)[0] + ".json"), "w") as f:
        json.dump(params, f, indent=2)

    base = os.path.splitext(filename)[0]
    update_cache(base, "simulated_area", params)
    update_cache(base, "original_area", params)

    job, queue_size = schedule_original_inference(base, None)
    print(job.id)
    job, queue_size = schedule_simulated_inference(base, None)
    print(job.id)

    return jsonify({"status": "success", "filename": filename})
