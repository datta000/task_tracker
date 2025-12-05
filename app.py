import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['JSON_SORT_KEYS'] = False

    cors_origins = os.getenv('CORS_ORIGINS', '*')
    # allow single origin or comma-separated list
    if ',' in cors_origins:
        CORS(app, origins=[o.strip() for o in cors_origins.split(',')])
    else:
        CORS(app, origins=cors_origins)

    # register blueprints
    from routes.auth import auth_bp
    from routes.tasks import tasks_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.registe  r_blueprint(tasks_bp, url_prefix='/tasks')

    @app.route('/')
    def index():
        return jsonify({"status": "ok", "message": "Task Tracker API"})

    return app

if __name__ == "__main__":
    # Development only
    app = create_app()
    app.run(host='127.0.0.1', port=int(os.getenv("PORT", 5000)), debug=True)
