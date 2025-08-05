import mysql.connector
import uuid
from datetime import datetime, timedelta
import json

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

def add_message_db(session_id, role, content, reference=None, checklist=None, mode='general', need_human=False):
    """
    添加消息到数据库
    
    Args:
        session_id: 会话ID
        role: 消息角色('user' 或 'ai')
        content: 消息内容
        reference: 参考资料(可选)
        checklist: 检查清单JSON字符串(可选)
        mode: 消息模式('general', 'rag', 'checklist', 'human_ticket')
        need_human: 是否需要人工介入(布尔值)
    
    Returns:
        (success, message_id, error): 成功状态、消息ID、错误信息
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, reference, checklist, mode, need_human) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session_id, role, content, reference, checklist, mode, 1 if need_human else 0)
        )
        message_id = cursor.lastrowid
        conn.commit()
        return True, message_id, None
    except mysql.connector.Error as err:
        return False, None, str(err)
    finally:
        cursor.close()
        conn.close()

def get_messages_db(session_id):
    """
    获取会话的所有消息
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT message_id, role, content, timestamp, reference, checklist, mode, need_human FROM messages WHERE session_id = %s ORDER BY timestamp ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        # 处理布尔值转换
        for message in messages:
            message['need_human'] = bool(message['need_human'])
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
        # 先删除 tickets 表中该 session 的所有工单
        cursor.execute("DELETE FROM tickets WHERE session_id = %s", (session_id,))
        # 再删除 messages 表中该 session 的所有消息
        cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        # 最后删除 chat_history 表中的 session
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


# ==================== 新增的消息管理相关函数 ====================

def update_message_reference(message_id, reference):
    """
    更新消息的参考资料
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE messages SET reference = %s WHERE message_id = %s",
            (reference, message_id)
        )
        conn.commit()
        return cursor.rowcount > 0, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def update_message_checklist(message_id, checklist):
    """
    更新消息的检查清单
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE messages SET checklist = %s WHERE message_id = %s",
            (checklist, message_id)
        )
        conn.commit()
        return cursor.rowcount > 0, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def update_checklist_item_status(message_id, item_index, checked):
    """
    更新单个checklist项目的状态
    
    Args:
        message_id: 消息ID
        item_index: checklist项目的索引
        checked: 是否已勾选
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 首先获取当前的checklist
        cursor.execute(
            "SELECT checklist FROM messages WHERE message_id = %s",
            (message_id,)
        )
        result = cursor.fetchone()
        if not result:
            return False, "Message not found"
        
        checklist_str = result[0]
        if not checklist_str:
            return False, "No checklist found"
        
        # 解析checklist JSON
        try:
            checklist = json.loads(checklist_str)
        except json.JSONDecodeError:
            return False, "Invalid checklist format"
        
        # 检查索引是否有效
        if item_index < 0 or item_index >= len(checklist):
            return False, "Invalid item index"
        
        # 更新指定项目的状态
        checklist[item_index]['done'] = checked
        
        # 将更新后的checklist保存回数据库
        updated_checklist_str = json.dumps(checklist)
        cursor.execute(
            "UPDATE messages SET checklist = %s WHERE message_id = %s",
            (updated_checklist_str, message_id)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def mark_message_need_human(message_id, need_human=True):
    """
    标记消息是否需要人工介入
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE messages SET need_human = %s WHERE message_id = %s",
            (1 if need_human else 0, message_id)
        )
        conn.commit()
        return cursor.rowcount > 0, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def get_messages_by_mode(mode, limit=100):
    """
    根据模式获取消息
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT m.*, ch.user_id FROM messages m "
            "JOIN chat_history ch ON m.session_id = ch.session_id "
            "WHERE m.mode = %s ORDER BY m.timestamp DESC LIMIT %s",
            (mode, limit)
        )
        messages = cursor.fetchall()
        # 处理布尔值转换
        for message in messages:
            message['need_human'] = bool(message['need_human'])
        return messages, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_messages_need_human():
    """
    获取所有需要人工介入的消息
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT m.*, ch.user_id, ui.first_name, ui.last_name, ui.email "
            "FROM messages m "
            "JOIN chat_history ch ON m.session_id = ch.session_id "
            "JOIN user_info ui ON ch.user_id = ui.user_id "
            "WHERE m.need_human = 1 ORDER BY m.timestamp DESC"
        )
        messages = cursor.fetchall()
        # 处理布尔值转换
        for message in messages:
            message['need_human'] = bool(message['need_human'])
        return messages, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_message_stats_by_mode():
    """
    获取各种模式的消息统计
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT mode, COUNT(*) as count, "
            "SUM(CASE WHEN need_human = 1 THEN 1 ELSE 0 END) as need_human_count "
            "FROM messages GROUP BY mode"
        )
        stats = cursor.fetchall()
        return stats, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


# ==================== 转人工工单管理相关函数 ====================

def save_ticket(session_id, staff_id, staff_email, content):
    """
    保存转人工请求工单
    
    Args:
        session_id: 会话ID
        staff_id: 员工ID
        staff_email: 员工邮箱
        content: 请求内容
    
    Returns:
        tuple: (ticket_id, error) - 成功返回工单ID，失败返回错误信息
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tickets (session_id, staff_id, staff_email, content) VALUES (%s, %s, %s, %s)",
            (session_id, staff_id, staff_email, content)
        )
        conn.commit()
        ticket_id = cursor.lastrowid
        return ticket_id, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_unfinished_tickets(limit=100):
    """
    获取所有未处理的工单
    
    Args:
        limit: 返回数量限制
        
    Returns:
        tuple: (tickets_list, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT t.*, ui.first_name, ui.last_name, ui.department, ui.role,
                   ch.title as session_title
            FROM tickets t
            JOIN user_info ui ON t.staff_id = ui.user_id
            JOIN chat_history ch ON t.session_id = ch.session_id
            WHERE t.is_finished = 0
            ORDER BY t.request_time DESC
            LIMIT %s
            """,
            (limit,)
        )
        tickets = cursor.fetchall()
        
        # 处理布尔值转换
        for ticket in tickets:
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return tickets, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_all_tickets(limit=500):
    """
    获取所有工单（包括已处理和未处理）
    
    Args:
        limit: 返回数量限制
        
    Returns:
        tuple: (tickets_list, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT t.*, ui.first_name, ui.last_name, ui.department, ui.role,
                   ch.title as session_title
            FROM tickets t
            JOIN user_info ui ON t.staff_id = ui.user_id
            JOIN chat_history ch ON t.session_id = ch.session_id
            ORDER BY t.request_time DESC
            LIMIT %s
            """,
            (limit,)
        )
        tickets = cursor.fetchall()
        
        # 处理布尔值转换
        for ticket in tickets:
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return tickets, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def finish_ticket(ticket_id, admin_notes=None):
    """
    完成工单处理
    
    Args:
        ticket_id: 工单ID
        admin_notes: 管理员处理备注（可选）
        
    Returns:
        tuple: (success, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tickets SET is_finished = 1, finished_time = NOW(), admin_notes = %s WHERE ticket_id = %s",
            (admin_notes, ticket_id)
        )
        conn.commit()
        return cursor.rowcount > 0, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def get_ticket_by_id(ticket_id):
    """
    根据ID获取单个工单详情
    
    Args:
        ticket_id: 工单ID
        
    Returns:
        tuple: (ticket_info, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT t.*, ui.first_name, ui.last_name, ui.department, ui.role, ui.email,
                   ch.title as session_title
            FROM tickets t
            JOIN user_info ui ON t.staff_id = ui.user_id
            JOIN chat_history ch ON t.session_id = ch.session_id
            WHERE t.ticket_id = %s
            """,
            (ticket_id,)
        )
        ticket = cursor.fetchone()
        
        if ticket:
            # 处理布尔值转换
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return ticket, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_tickets_stats():
    """
    获取工单统计信息
    
    Returns:
        tuple: (stats, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_tickets,
                SUM(CASE WHEN is_finished = 0 THEN 1 ELSE 0 END) as pending_tickets,
                SUM(CASE WHEN is_finished = 1 THEN 1 ELSE 0 END) as finished_tickets,
                COUNT(CASE WHEN request_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as recent_tickets
            FROM tickets
            """
        )
        stats = cursor.fetchone()
        return stats, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_tickets_by_staff(staff_id, limit=50):
    """
    获取特定员工的工单列表
    
    Args:
        staff_id: 员工ID
        limit: 返回数量限制
        
    Returns:
        tuple: (tickets_list, error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT t.*, ch.title as session_title
            FROM tickets t
            JOIN chat_history ch ON t.session_id = ch.session_id
            WHERE t.staff_id = %s
            ORDER BY t.request_time DESC
            LIMIT %s
            """,
            (staff_id, limit)
        )
        tickets = cursor.fetchall()
        
        # 处理布尔值转换
        for ticket in tickets:
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return tickets, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()
