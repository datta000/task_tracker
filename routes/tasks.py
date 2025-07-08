from flask import Blueprint, request, jsonify
from db import get_db_connection
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

tasks_bp = Blueprint('tasks', __name__)

# 🔐 JWT token verification
def verify_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        token = auth_header.split(" ")[1]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["user_id"]
    except jwt.ExpiredSignatureError:
        return "expired"
    except Exception:
        return None

# ✅ GET /tasks - Fetch all tasks
@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ GET /tasks/<id> - Fetch task by ID
@tasks_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        cursor.close()
        conn.close()
        if task:
            return jsonify(task)
        else:
            return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ POST /tasks - Create a new task (🔐 Protected)
@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    user_id = verify_token()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    if user_id == "expired":
        return jsonify({"error": "Token expired"}), 401

    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")

        if not title or not description:
            return jsonify({"error": "Title and description required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description) VALUES (%s, %s)",
            (title, description)
        )
        conn.commit()
        task_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "id": task_id,
            "title": title,
            "description": description,
            "status": "pending"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ PUT /tasks/<id> - Update a task (🔐 Protected)
@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user_id = verify_token()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    if user_id == "expired":
        return jsonify({"error": "Token expired"}), 401

    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        status = data.get("status")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET title = %s, description = %s, status = %s WHERE id = %s",
            (title, description, status, task_id)
        )
        conn.commit()
        updated = cursor.rowcount
        cursor.close()
        conn.close()

        if updated == 0:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"message": "Task updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ DELETE /tasks/<id> - Delete a task (🔐 Protected)
@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user_id = verify_token()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    if user_id == "expired":
        return jsonify({"error": "Token expired"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        deleted = cursor.rowcount
        cursor.close()
        conn.close()

        if deleted == 0:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"message": "Task deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
