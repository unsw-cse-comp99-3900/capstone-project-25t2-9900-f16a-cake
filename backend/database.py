import mysql.connector
import uuid
from datetime import datetime, timedelta

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


def get_all_admins():
    """获取所有admin用户的邮箱"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT email, first_name, last_name FROM user_info WHERE is_admin = 1")
        admins = cursor.fetchall()
        return admins, None
    except Exception as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def record_user_login(user_id, ip_address=None, user_agent=None):
    """记录用户登录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_login_logs (user_id, ip_address, user_agent) VALUES (%s, %s, %s)",
            (user_id, ip_address, user_agent)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def get_daily_login_stats(days=7):
    """获取每日登录统计"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 获取最近N天的每日登录次数，排除admin用户
        cursor.execute("""
            SELECT 
                DATE(ull.login_time) as date, 
                COUNT(*) as login_count
            FROM user_login_logs ull
            JOIN user_info ui ON ull.user_id = ui.user_id
            WHERE ull.login_time >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            AND ui.is_admin = 0
            GROUP BY DATE(ull.login_time)
            ORDER BY date
        """, (days - 1,))
        
        results = cursor.fetchall()
        
        # 确保返回完整的7天数据，没有记录的日期返回0
        stats = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            found = False
            for result in results:
                if result['date'].strftime('%Y-%m-%d') == date:
                    stats.append({
                        'date': date,
                        'active_users': result['login_count']
                    })
                    found = True
                    break
            if not found:
                stats.append({
                    'date': date,
                    'active_users': 0
                })
        
        # 按日期正序排列
        stats.reverse()
        return stats, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def save_pdf_document(title, keywords, keywords_encoded, pdf_path, year, uploader_id, file_size):
    """保存PDF文档元数据到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO pdf_documents (title, keywords, keywords_encoded, pdf_path, year, uploader_id, file_size) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (title, keywords, keywords_encoded, pdf_path, year, uploader_id, file_size)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def get_all_pdf_documents():
    """获取所有PDF文档"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pdf_documents ORDER BY upload_time DESC")
        documents = cursor.fetchall()
        return documents, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_pdf_documents_for_search():
    """获取用于搜索的PDF文档（包含编码数据）"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title, keywords, keywords_encoded, pdf_path, year FROM pdf_documents")
        documents = cursor.fetchall()
        return documents, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def delete_pdf_document(document_id):
    """删除PDF文档记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM pdf_documents WHERE id = %s", (document_id,))
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def update_keywords_encoded(document_id, keywords_encoded):
    """更新文档的关键词编码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE pdf_documents SET keywords_encoded = %s WHERE id = %s",
            (keywords_encoded, document_id)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_keywords_from_db():
    """从数据库获取所有关键词"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT keyword FROM all_keywords ORDER BY keyword")
        keywords = [row[0] for row in cursor.fetchall()]
        return keywords, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

def add_keywords_to_db(keywords_list):
    """添加新关键词到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        added_count = 0
        for keyword in keywords_list:
            try:
                cursor.execute("INSERT INTO all_keywords (keyword) VALUES (%s)", (keyword,))
                added_count += 1
            except mysql.connector.IntegrityError:
                # 关键词已存在，忽略
                pass
        conn.commit()
        return True, f"Added {added_count} new keywords"
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def update_all_documents_encoding():
    """更新所有文档的关键词编码"""
    from search import multi_hot_encode
    import json
    
    # 获取所有关键词
    all_keywords, error = get_all_keywords_from_db()
    if error:
        return False, f"Failed to get keywords: {error}"
    
    # 获取所有文档
    documents, error = get_all_pdf_documents()
    if error:
        return False, f"Failed to get documents: {error}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        updated_count = 0
        for doc in documents:
            keywords = doc['keywords']
            if not keywords:
                continue
                
            # 重新编码关键词
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            keywords_encoded = multi_hot_encode(keyword_list)
            keywords_encoded_json = json.dumps(keywords_encoded)
            
            # 更新数据库
            cursor.execute(
                "UPDATE pdf_documents SET keywords_encoded = %s WHERE id = %s",
                (keywords_encoded_json, doc['id'])
            )
            updated_count += 1
        
        conn.commit()
        return True, f"Updated {updated_count} documents"
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def rebuild_keywords_database():
    """重新构建关键词数据库（从剩余文档中提取）"""
    # 获取所有文档的关键词
    documents, error = get_all_pdf_documents()
    if error:
        return False, f"Failed to get documents: {error}"
    
    # 收集所有关键词
    all_keywords = set()
    for doc in documents:
        keywords = doc.get('keywords', '')
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            all_keywords.update(keyword_list)
    
    # 清空现有关键词表
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM all_keywords")
        
        # 插入新的关键词
        for keyword in sorted(all_keywords):
            cursor.execute("INSERT INTO all_keywords (keyword) VALUES (%s)", (keyword,))
        
        conn.commit()
        return True, f"Rebuilt keywords database with {len(all_keywords)} keywords"
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()
