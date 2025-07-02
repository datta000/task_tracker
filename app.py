from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='ritaban',
            database='task_tracker',
            connection_timeout=5  # ⏱️ Prevent hanging forever
        )
        return connection
    except Error as e:
        print("❌ Error connecting to MySQL:", e)
        return None

@app.route('/tasks', methods=['POST'])
def create_task():
    try:
        print("🔧 POST /tasks called")

        data = request.get_json()
        print("✅ Data received:", data)

        title = data.get('title')
        description = data.get('description', '')
        status = data.get('status', 'pending')

        print("📦 Extracted:", title, description, status)

        if not title:
            print("❌ Title is missing")
            return jsonify({'error': 'Title is required'}), 400

        if status not in ['pending', 'completed']:
            print("❌ Invalid status")
            return jsonify({'error': 'Invalid status'}), 400

        print("🔌 Connecting to DB...")
        conn = get_db_connection()
        if conn is None:
            print("❌ DB connection failed")
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        print("📝 Inserting into DB...")
        query = """
            INSERT INTO tasks (title, description, status)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (title, description, status))
        conn.commit()

        task_id = cursor.lastrowid
        print(f"✅ Task inserted with ID: {task_id}")

        cursor.close()
        conn.close()

        return jsonify({
            'id': task_id,
            'title': title,
            'description': description,
            'status': status
        }), 201

    except Exception as e:
        print("💥 Error in POST /tasks:", e)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    title = data.get('title')
    description = data.get('description')
    status = data.get('status')

    if status and status not in ['pending', 'completed']:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if not task:
        cursor.close()
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    updates = []
    values = []

    if title:
        updates.append("title = %s")
        values.append(title)
    if description:
        updates.append("description = %s")
        values.append(description)
    if status:
        updates.append("status = %s")
        values.append(status)

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    values.append(task_id)
    sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
    cursor.execute(sql, tuple(values))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Task updated successfully"}), 200

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if not task:
        cursor.close()
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
