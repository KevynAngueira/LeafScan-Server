from flask import Flask
from flask_cors import CORS
from core.paths import ensure_dirs
from routes import register_routes

def create_app():
    app = Flask(__name__, static_folder="static")
    CORS(app)
    ensure_dirs()
    register_routes(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
