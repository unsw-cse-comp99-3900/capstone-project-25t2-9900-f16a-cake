"""
Database Management Module for Chat System

This module provides comprehensive database operations for a chat system with the following features:
- User management and authentication
- Chat session management
- Message storage and retrieval
- PDF document management with keyword encoding
- Human intervention ticket system
- User activity logging and statistics

Database Schema:
- user_info: User account information and permissions
- chat_history: Chat session metadata
- messages: Individual chat messages with metadata
- pdf_documents: PDF document storage with keyword encoding
- all_keywords: Keyword vocabulary for document search
- tickets: Human intervention request tickets
- user_login_logs: User login activity tracking

Author: Capstone Project Team
Version: 1.0
Date: 2024
"""

import mysql.connector
import uuid
from datetime import datetime, timedelta
import json

# Database configuration
# Note: Update these values according to your local database setup
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Update with your database password
    'database': 'chat_system'
}

def get_db_connection():
    """
    Create and return a new database connection
    
    Returns:
        mysql.connector.connection: Database connection object
    """
    return mysql.connector.connect(**db_config)

def get_user(username):
    """
    Retrieve user information by username
    
    Args:
        username (str): User ID to search for
        
    Returns:
        dict: User information dictionary or None if not found
    """
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
    """
    Create a new chat session for a user
    
    Args:
        user_id (str): ID of the user starting the session
        title (str): Session title, defaults to "Untitled Session"
        
    Returns:
        tuple: (session_id, error) - session ID on success, error message on failure
    """
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
    Add a message to the database
    
    Args:
        session_id (str): Session ID for the message
        role (str): Message role ('user' or 'ai')
        content (str): Message content text
        reference (str, optional): Reference materials
        checklist (str, optional): Checklist JSON string
        mode (str): Message mode ('general', 'rag', 'checklist', 'human_ticket')
        need_human (bool): Whether human intervention is needed
    
    Returns:
        tuple: (success, message_id, error) - success status, message ID, error message
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
    Retrieve all messages for a specific session
    
    Args:
        session_id (str): Session ID to retrieve messages for
        
    Returns:
        tuple: (messages_list, error) - list of messages or error message
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT message_id, role, content, timestamp, reference, checklist, mode, need_human FROM messages WHERE session_id = %s ORDER BY timestamp ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        # Convert boolean values
        for message in messages:
            message['need_human'] = bool(message['need_human'])
        return messages, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

def session_exists(session_id):
    """
    Check if a session exists in the database
    
    Args:
        session_id (str): Session ID to check
        
    Returns:
        bool: True if session exists, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM chat_history WHERE session_id = %s", (session_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def check_or_create_session(session_id, user_id, title="New Chat"):
    """
    Check if session exists, create if it doesn't
    
    Args:
        session_id (str): Session ID to check/create
        user_id (str): User ID for the session
        title (str): Session title
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
    if session_exists(session_id):
        return True, None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # chat_history user_id is constrained by foreign key user_info(user_id)
        # so we need to ensure user_id is valid
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
    """
    Get all chat sessions for a specific user
    
    Args:
        user_id (str): User ID to get sessions for
        
    Returns:
        tuple: (sessions_list, error) - list of sessions or error message
    """
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
    """
    Update the title of a chat session
    
    Args:
        session_id (str): Session ID to update
        new_title (str): New title for the session
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
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
    """
    Delete a chat session and all related data
    
    Args:
        session_id (str): Session ID to delete
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First delete all tickets for this session
        cursor.execute("DELETE FROM tickets WHERE session_id = %s", (session_id,))
        # Then delete all messages for this session
        cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        # Finally delete the session from chat_history
        cursor.execute("DELETE FROM chat_history WHERE session_id = %s", (session_id,))
        conn.commit()
        return True, None
    except Exception as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_admins():
    """
    Get all admin users from the database
    
    Returns:
        tuple: (admins_list, error) - list of admin users or error message
    """
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
    """
    Record user login activity
    
    Args:
        user_id (str): User ID who logged in
        ip_address (str, optional): IP address of the login
        user_agent (str, optional): User agent string
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
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
    """
    Get daily login statistics for the specified number of days
    
    Args:
        days (int): Number of days to get stats for (default: 7)
        
    Returns:
        tuple: (stats_list, error) - list of daily stats or error message
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get daily login counts for the last N days, excluding admin users
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
        
        # Ensure complete N days of data, return 0 for dates with no records
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
        
        # Sort by date in ascending order
        stats.reverse()
        return stats, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def save_pdf_document(title, keywords, keywords_encoded, pdf_path, document_date, uploader_id, file_size):
    """
    Save PDF document metadata to database
    
    Args:
        title (str): Document title
        keywords (str): Comma-separated keywords
        keywords_encoded (str): JSON string of encoded keywords
        pdf_path (str): File path to the PDF
        document_date (str): Document date
        uploader_id (str): ID of the user who uploaded the document
        file_size (int): File size in bytes
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO pdf_documents (title, keywords, keywords_encoded, pdf_path, document_date, uploader_id, file_size) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (title, keywords, keywords_encoded, pdf_path, document_date, uploader_id, file_size)
        )
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


def get_all_pdf_documents():
    """
    Get all PDF documents from database
    
    Returns:
        tuple: (documents_list, error) - list of documents or error message
    """
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
    """
    Get PDF documents for search operations (includes encoded data)
    
    Returns:
        tuple: (documents_list, error) - list of documents or error message
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title, keywords, keywords_encoded, pdf_path, document_date FROM pdf_documents")
        documents = cursor.fetchall()
        return documents, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def delete_pdf_document(document_id):
    """
    Delete a PDF document record from database
    
    Args:
        document_id (int): ID of the document to delete
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
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
    """
    Update the keyword encoding for a document
    
    Args:
        document_id (int): ID of the document to update
        keywords_encoded (str): New encoded keywords JSON string
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
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
    """
    Get all keywords from the database
    
    Returns:
        tuple: (keywords_list, error) - list of keywords or error message
    """
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
    """
    Add new keywords to the database
    
    Args:
        keywords_list (list): List of keywords to add
        
    Returns:
        tuple: (success, message) - success status and result message
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        added_count = 0
        for keyword in keywords_list:
            try:
                cursor.execute("INSERT INTO all_keywords (keyword) VALUES (%s)", (keyword,))
                added_count += 1
            except mysql.connector.IntegrityError:
                # Keyword already exists, ignore
                pass
        conn.commit()
        return True, f"Added {added_count} new keywords"
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def update_all_documents_encoding():
    """
    Update keyword encoding for all documents
    
    Returns:
        tuple: (success, message) - success status and result message
    """
    from search import multi_hot_encode
    import json
    
    # Get all keywords
    all_keywords, error = get_all_keywords_from_db()
    if error:
        return False, f"Failed to get keywords: {error}"
    
    # Get all documents
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
                
            # Re-encode keywords
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            keywords_encoded = multi_hot_encode(keyword_list)
            keywords_encoded_json = json.dumps(keywords_encoded)
            
            # Update database
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
    """
    Rebuild the keywords database from remaining documents
    
    Returns:
        tuple: (success, message) - success status and result message
    """
    # Get keywords from all documents
    documents, error = get_all_pdf_documents()
    if error:
        return False, f"Failed to get documents: {error}"
    
    # Collect all keywords
    all_keywords = set()
    for doc in documents:
        keywords = doc.get('keywords', '')
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            all_keywords.update(keyword_list)
    
    # Clear existing keywords table
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM all_keywords")
        
        # Insert new keywords
        for keyword in sorted(all_keywords):
            cursor.execute("INSERT INTO all_keywords (keyword) VALUES (%s)", (keyword,))
        
        conn.commit()
        return True, f"Rebuilt keywords database with {len(all_keywords)} keywords"
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()


# ==================== Message Management Functions ====================

def update_message_reference(message_id, reference):
    """
    Update the reference materials for a message
    
    Args:
        message_id (int): ID of the message to update
        reference (str): New reference materials
        
    Returns:
        tuple: (success, error) - success status and error message if any
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
    Update the checklist for a message
    
    Args:
        message_id (int): ID of the message to update
        checklist (str): New checklist JSON string
        
    Returns:
        tuple: (success, error) - success status and error message if any
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
    Update the status of a specific checklist item
    
    Args:
        message_id (int): ID of the message containing the checklist
        item_index (int): Index of the checklist item to update
        checked (bool): New checked status
        
    Returns:
        tuple: (success, error) - success status and error message if any
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get current checklist
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
        
        # Parse checklist JSON
        try:
            checklist = json.loads(checklist_str)
        except json.JSONDecodeError:
            return False, "Invalid checklist format"
        
        # Check if index is valid
        if item_index < 0 or item_index >= len(checklist):
            return False, "Invalid item index"
        
        # Update the status of the specified item
        checklist[item_index]['done'] = checked
        
        # Save the updated checklist back to database
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
    Mark whether a message needs human intervention
    
    Args:
        message_id (int): ID of the message to mark
        need_human (bool): Whether human intervention is needed
        
    Returns:
        tuple: (success, error) - success status and error message if any
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
    Get messages by specific mode
    
    Args:
        mode (str): Message mode to filter by
        limit (int): Maximum number of messages to return
        
    Returns:
        tuple: (messages_list, error) - list of messages or error message
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
        # Convert boolean values
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
    Get all messages that need human intervention
    
    Returns:
        tuple: (messages_list, error) - list of messages or error message
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
        # Convert boolean values
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
    Get message statistics grouped by mode
    
    Returns:
        tuple: (stats_list, error) - list of statistics or error message
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


# ==================== Human Intervention Ticket Management Functions ====================

def save_ticket(session_id, staff_id, staff_email, content):
    """
    Save a human intervention request ticket
    
    Args:
        session_id (str): Session ID for the ticket
        staff_id (str): Staff member ID
        staff_email (str): Staff member email
        content (str): Request content
    
    Returns:
        tuple: (ticket_id, error) - ticket ID on success, error message on failure
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
    Get all unfinished tickets
    
    Args:
        limit (int): Maximum number of tickets to return
        
    Returns:
        tuple: (tickets_list, error) - list of tickets or error message
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
        
        # Convert boolean values
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
    Get all tickets (including finished and unfinished)
    
    Args:
        limit (int): Maximum number of tickets to return
        
    Returns:
        tuple: (tickets_list, error) - list of tickets or error message
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
        
        # Convert boolean values
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
    Mark a ticket as finished
    
    Args:
        ticket_id (int): ID of the ticket to finish
        admin_notes (str, optional): Admin processing notes
        
    Returns:
        tuple: (success, error) - success status and error message if any
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
    Get a single ticket by ID
    
    Args:
        ticket_id (int): ID of the ticket to retrieve
        
    Returns:
        tuple: (ticket_info, error) - ticket information or error message
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
            # Convert boolean values
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return ticket, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()


def get_tickets_stats():
    """
    Get ticket statistics
    
    Returns:
        tuple: (stats, error) - statistics dictionary or error message
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
    Get tickets for a specific staff member
    
    Args:
        staff_id (str): Staff member ID
        limit (int): Maximum number of tickets to return
        
    Returns:
        tuple: (tickets_list, error) - list of tickets or error message
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
        
        # Convert boolean values
        for ticket in tickets:
            ticket['is_finished'] = bool(ticket['is_finished'])
            
        return tickets, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()
