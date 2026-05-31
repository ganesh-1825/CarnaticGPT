from backend.database import get_db_connection
from backend.logger import logger

def record_user_feedback(message_id: int, rating: int, comment: str = None):
    """Saves user upvote/downvote and custom notes to SQL database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if feedback already exists for this message
        cursor.execute("SELECT id FROM feedback WHERE message_id = ?", (message_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                "UPDATE feedback SET rating = ?, comment = ?, created_at = CURRENT_TIMESTAMP WHERE message_id = ?",
                (rating, comment, message_id)
            )
            logger.info(f"Updated feedback rating {rating} for message_id {message_id}")
        else:
            cursor.execute(
                "INSERT INTO feedback (message_id, rating, comment) VALUES (?, ?, ?)",
                (message_id, rating, comment)
            )
            logger.info(f"Saved new feedback rating {rating} for message_id {message_id}")
            
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error in record_user_feedback: {e}")
        return False
    finally:
        conn.close()
