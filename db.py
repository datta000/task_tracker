import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='ritaban',
            database='task_tracker',
            connection_timeout=5 
        )
        return connection
    except Error as e:
        print("❌ Error connecting to MySQL:", e)
        return None