from backend.database import get_db_connection
from backend.logger import logger
import json

def create_conversation_if_not_exists(conv_id: str, user_id: int, title: str = "New Chat"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
                (conv_id, user_id, title)
            )
            conn.commit()
            logger.info(f"Created conversation session: {conv_id} for user_id {user_id}")
    except Exception as e:
        logger.error(f"Error in create_conversation_if_not_exists: {e}")
    finally:
        conn.close()

def save_chat_message(conv_id: str, sender: str, content: str, citations: list = None, confidence: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    citations_json = json.dumps(citations, ensure_ascii=False) if citations else None
    
    try:
        cursor.execute(
            "INSERT INTO messages (conversation_id, sender, content, citations, confidence) VALUES (?, ?, ?, ?, ?)",
            (conv_id, sender, content, citations_json, confidence)
        )
        conn.commit()
        message_id = cursor.lastrowid
        # Proactively update conversation title dynamically to the first query
        if sender == "user":
            cursor.execute("SELECT title FROM conversations WHERE id = ?", (conv_id,))
            conv_row = cursor.fetchone()
            if conv_row and conv_row["title"] == "New Chat":
                title = content[:30] + "..." if len(content) > 30 else content
                cursor.execute("UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title, conv_id))
            else:
                cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conv_id,))
            conn.commit()
            
        return message_id
    except Exception as e:
        logger.error(f"Error in save_chat_message: {e}")
        return None
    finally:
        conn.close()

def get_conversation_history(conv_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, sender, content, citations, confidence, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,)
        )
        rows = cursor.fetchall()
        history = []
        for r in rows:
            citations_list = []
            if r["citations"]:
                try:
                    citations_list = json.loads(r["citations"])
                except Exception:
                    pass
            # Backwards compatibility check for older logs
            conf_val = None
            try:
                conf_val = r["confidence"]
            except Exception:
                pass
            history.append({
                "id": r["id"],
                "sender": r["sender"],
                "content": r["content"],
                "citations": citations_list,
                "confidence": conf_val,
                "created_at": r["created_at"]
            })
        return history
    finally:
        conn.close()

def get_user_conversations(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, title, is_pinned, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY is_pinned DESC, updated_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        # Ensure older databases lacking these columns don't crash by using .get() or checking keys
        return [{
            "id": r["id"], 
            "title": r["title"], 
            "is_pinned": bool(r["is_pinned"]) if "is_pinned" in r.keys() else False,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"] if "updated_at" in r.keys() else r["created_at"]
        } for r in rows]
    finally:
        conn.close()

def delete_user_conversation(conv_id: str, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        return False
    finally:
        conn.close()

def rename_conversation(conv_id: str, user_id: int, new_title: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE conversations SET title = ? WHERE id = ? AND user_id = ?", (new_title, conv_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to rename conversation: {e}")
        return False
    finally:
        conn.close()

def toggle_pin_conversation(conv_id: str, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT is_pinned FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        row = cursor.fetchone()
        if not row:
            return False
            
        new_val = 0 if row["is_pinned"] else 1
        cursor.execute("UPDATE conversations SET is_pinned = ? WHERE id = ? AND user_id = ?", (new_val, conv_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to toggle pin: {e}")
        return False
    finally:
        conn.close()
