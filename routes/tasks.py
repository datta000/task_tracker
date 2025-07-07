from flask import Blueprint, request, jsonify
from db import get_db_connection

tasks_bp = Blueprint('tasks', __name__)

# GET /tasks - Fetch all tasks
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

# GET /tasks/<id> - Fetch task by ID
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

# POST /tasks - Create a new task
@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
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

# PUT /tasks/<id> - Update an existing task
@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
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

# DELETE /tasks/<id> - Delete a task
@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
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
