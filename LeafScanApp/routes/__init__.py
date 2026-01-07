from flask import Blueprint
from .send_routes import send_bp
from .display_routes import display_bp
from .inference_routes import inference_bp
from .test_routes import test_bp
from .scheduler_routes import scheduler_bp

def register_routes(app):
    app.register_blueprint(send_bp)
    app.register_blueprint(display_bp)
    app.register_blueprint(inference_bp)
    app.register_blueprint(test_bp)
