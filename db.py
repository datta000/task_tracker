import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling

load_dotenv()

dbconfig = { 
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "task_tracker"),
    "connection_timeout": int(os.getenv("DB_CONN_TIMEOUT", "5")),
    "autocommit": False
}

POOL_NAME = "task_tracker_pool"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

connection_pool = None
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name=POOL_NAME,
        pool_size=POOL_SIZE,
        **dbconfig
    )
except Exception as e:
    print("❌ DB pool creation failed:", e)
    connection_pool = None

def get_db_connection():
    """
    Returns a mysql.connector connection (from pool if available).
    Caller must close() the connection when finished.
    """
    try:
        if connection_pool:
            return connection_pool.get_connection()
        return mysql.connector.connect(**dbconfig)
    except Error as e:
        print("❌ Error connecting to MySQL:", e)
        return None
