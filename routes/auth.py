from flask import Blueprint, request, jsonify, current_app
from db import get_db_connection
import bcrypt
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__)

def hash_password(plain_password: str) -> bytes:
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

def check_password(plain_password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Expected JSON: { "username": "...", "password": "...", "role": "user" }
    role optional; default "user". Admins should be created manually or via protected endpoint.
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    hashed = hash_password(password)
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500

    try:
        cursor = conn.cursor()
        # check existing user
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "username already exists"}), 400

        cursor.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, NOW())",
            (username, hashed, role)
        )
        conn.commit()
        return jsonify({"message": "user registered"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Expected JSON: {"username": "...", "password": "..."}
    Returns: { "token": "...", "expires_in": <seconds> }
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s", (username,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "invalid credentials"}), 401

        stored_hash = row['password_hash']
        # stored_hash is bytes when inserted as bytes; ensure proper type
        if isinstance(stored_hash, memoryview):
            stored_hash = stored_hash.tobytes()
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        if not check_password(password, stored_hash):
            return jsonify({"error": "invalid credentials"}), 401

        secret = current_app.config.get('SECRET_KEY')
        expires_delta = int(os.getenv('JWT_EXPIRES_SECONDS', '3600'))
        now = datetime.datetime.utcnow()
        payload = {
            "sub": row['id'],
            "username": row['username'],
            "role": row['role'],
            "iat": now,
            "exp": now + datetime.timedelta(seconds=expires_delta)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return jsonify({"token": token, "expires_in": expires_delta}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
