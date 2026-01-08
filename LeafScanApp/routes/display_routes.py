import os, json
from flask import Blueprint, request, jsonify, current_app
from core.paths import IMAGE_DIR, VIDEO_DIR, PARAMS_DIR

display_bp = Blueprint("display", __name__)

@display_bp.route('/display/image')
def display_images():
    received_images = list_image_files(IMAGE_DIR)

    if received_images:
        images_html = '<ul>'
        for image in received_images:
            images_html += f'<li><img src="/{IMAGE_DIR}/{image}" alt="{image}" width="150" height="150"><br><strong>{image}</strong></li>'
        images_html += '</ul>'
        return render_template_string(images_html)
    else:
        return "<p>No images have been received yet.</p>"

@display_bp.route('/display/video')
def display_videos():
    received_videos = list_video_files(VIDEO_DIR)

    if received_videos:
        videos_html = '<ul>'
        for video in received_videos:
            videos_html += f'<li><video controls src="/{VIDEO_DIR}/{video}" alt="{video}" width="150" height="150" controls><br><strong>{video}</strong></video></li>'
        videos_html += '</ul>'
        return render_template_string(videos_html)
    else:
        return "<p>No videos have been received yet.</p>"

def list_image_files(directory):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(directory) if f.lower().endswith(image_extensions)]
    current_app.logger.info(f'TEST: {image_files}')
    return image_files

def list_video_files(directory):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm')
    video_files = [f for f in os.listdir(directory) if f.lower().endswith(video_extensions)]
    current_app.logger.info(f'Video files: {video_files}')
    return video_files