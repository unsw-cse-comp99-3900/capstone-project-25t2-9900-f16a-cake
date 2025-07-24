import mysql.connector
import uuid

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # 需要是自己数据库的密码
    'database': 'chat_system'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user_info WHERE user_id=%s", (username,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        conn.close()

def start_session_db(user_id, title="Untitled Session"):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_history (user_id, session_id, title) VALUES (%s, %s, %s)",
            (user_id, session_id, title)
        )
        conn.commit()
        return session_id, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

def add_message_db(session_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_messages_db(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = %s ORDER BY timestamp ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        return messages, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

def session_exists(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM chat_history WHERE session_id = %s", (session_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def check_or_create_session(session_id, user_id, title="New Chat"):
    if session_exists(session_id):
        return True, None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # chat_history中的user_id也受外键user_info(user_id)的约束
        # 所以需要确保user_id是有效的
        cursor.execute(
            "INSERT INTO chat_history (user_id, session_id, title) VALUES (%s, %s, %s)",
            (user_id, session_id, title)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_sessions_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT session_id, title, created_at FROM chat_history WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        sessions = cursor.fetchall()
        return sessions, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

def update_session_title(session_id, new_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE chat_history SET title = %s WHERE session_id = %s",
            (new_title, session_id)
        )
        conn.commit()
        return True, None
    except Exception as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 先删除 messages 表中该 session 的所有消息
        cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        # 再删除 chat_history 表中的 session
        cursor.execute("DELETE FROM chat_history WHERE session_id = %s", (session_id,))
        conn.commit()
        return True, None
    except Exception as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()
