from flask import Blueprint, request, jsonify, current_app, g
from db import get_db_connection
from middleware import login_required, role_required

tasks_bp = Blueprint('tasks', __name__)

# Helper: convert DB row (tuple) to dict
def row_to_task(row, cursor):
    # depends on cursor.column_names
    return dict(zip(cursor.column_names, row))

@tasks_bp.route('/', methods=['GET'])
@login_required
def list_tasks():
    """
    Optional query params:
      - assigned_to (user id)
      - status (open/done)
      - page, limit
    """
    assigned_to = request.args.get('assigned_to')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    offset = (page - 1) * limit

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500

    try:
        cursor = conn.cursor()
        sql = "SELECT id, title, description, status, assigned_to, created_at, updated_at FROM tasks WHERE 1=1"
        params = []
        if assigned_to:
            sql += " AND assigned_to = %s"
            params.append(assigned_to)
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        tasks = [row_to_task(row, cursor) for row in rows]
        return jsonify({"tasks": tasks}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@tasks_bp.route('/', methods=['POST'])
@login_required
def create_task():
    """
    Body: { "title": "...", "description": "...", "assigned_to": <id> (optional) }
    """
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description', '')
    assigned_to = data.get('assigned_to')

    if not title:
        return jsonify({"error": "title is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, status, assigned_to, created_at, updated_at) VALUES (%s,%s,%s,%s,NOW(),NOW())",
            (title, description, 'open', assigned_to)
        )
        conn.commit()
        task_id = cursor.lastrowid
        return jsonify({"message": "task created", "id": task_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, status, assigned_to, created_at, updated_at FROM tasks WHERE id=%s", (task_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        return jsonify({"task": row_to_task(row, cursor)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@tasks_bp.route('/<int:task_id>', methods=['PUT', 'PATCH'])
@login_required
def update_task(task_id):
    """
    Body may contain any of: title, description, status, assigned_to
    """
    data = request.get_json() or {}
    allowed = ['title', 'description', 'status', 'assigned_to']
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        return jsonify({"error": "no fields to update"}), 400

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    params = list(updates.values())
    params.append(task_id)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor()
        sql = f"UPDATE tasks SET {set_clause}, updated_at = NOW() WHERE id = %s"
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "not found"}), 404
        return jsonify({"message": "updated"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@role_required('admin')  # only admin can delete tasks
def delete_task(task_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "not found"}), 404
        return jsonify({"message": "deleted"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass