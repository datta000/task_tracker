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

