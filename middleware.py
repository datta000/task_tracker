from functools import wraps
from flask import request,Blueprint, jsonify
import jwt
import os
from dotenv import load_dotenv
from middleware import role_required

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                try:
                    token = request.headers['Authorization'].split()[1]
                except IndexError:
                    return jsonify({"error": "Malformed token"}), 401

            if not token:
                return jsonify({"error": "Missing token"}), 401

            try:
                decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if decoded.get("role") != required_role:
                    return jsonify({"error": "Forbidden"}), 403
            except Exception as e:
                return jsonify({"error": str(e)}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator



tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/admin-only', methods=['GET'])
@role_required('admin')  # 👈 Only admin can access
def admin_route():
    return jsonify({"message": "Hello Admin! You have access."})

@tasks_bp.route('/user-task', methods=['GET'])
@role_required('user')  # 👈 Only regular users can access
def user_route():
    return jsonify({"message": "Hello User! You have access."})
