"""
Database models for tracking processed comments and messages.
"""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ProcessedComment(Base):
    """Track comments that have been processed/replied to."""
    __tablename__ = "processed_comments"
    
    id = Column(String(255), primary_key=True)  # Facebook comment ID
    post_id = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    from_name = Column(String(255), nullable=True)
    from_id = Column(String(255), nullable=True)
    our_reply = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    replied = Column(Boolean, default=False)
    error = Column(Text, nullable=True)


class ProcessedMessage(Base):
    """Track messages/conversations that have been processed."""
    __tablename__ = "processed_messages"
    
    id = Column(String(255), primary_key=True)  # Facebook message ID
    conversation_id = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    from_name = Column(String(255), nullable=True)
    from_id = Column(String(255), nullable=True)
    our_reply = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    replied = Column(Boolean, default=False)
    error = Column(Text, nullable=True)


class BotActivity(Base):
    """Track bot activity and runs."""
    __tablename__ = "bot_activity"
    
    id = Column(String(255), primary_key=True)
    activity_type = Column(String(50), nullable=False)  # 'comment_check', 'message_check', 'reply_sent'
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_database():
    """Initialize the database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db_session():
    """Get a database session."""
    return SessionLocal()


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self):
        init_database()
    
    def is_comment_processed(self, comment_id: str) -> bool:
        """Check if a comment has already been processed."""
        session = get_db_session()
        try:
            exists = session.query(ProcessedComment).filter_by(id=comment_id).first()
            return exists is not None
        finally:
            session.close()
    
    def mark_comment_processed(
        self, 
        comment_id: str, 
        post_id: str,
        message: str = None,
        from_name: str = None,
        from_id: str = None,
        our_reply: str = None,
        replied: bool = False,
        error: str = None
    ):
        """Mark a comment as processed."""
        session = get_db_session()
        try:
            comment = ProcessedComment(
                id=comment_id,
                post_id=post_id,
                message=message,
                from_name=from_name,
                from_id=from_id,
                our_reply=our_reply,
                replied=replied,
                error=error,
                processed_at=datetime.utcnow()
            )
            session.merge(comment)  # Use merge to handle updates
            session.commit()
            logger.debug(f"Marked comment {comment_id} as processed")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark comment as processed: {e}")
        finally:
            session.close()
    
    def is_message_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed."""
        session = get_db_session()
        try:
            exists = session.query(ProcessedMessage).filter_by(id=message_id).first()
            return exists is not None
        finally:
            session.close()
    
    def mark_message_processed(
        self,
        message_id: str,
        conversation_id: str,
        message: str = None,
        from_name: str = None,
        from_id: str = None,
        our_reply: str = None,
        replied: bool = False,
        error: str = None
    ):
        """Mark a message as processed."""
        session = get_db_session()
        try:
            msg = ProcessedMessage(
                id=message_id,
                conversation_id=conversation_id,
                message=message,
                from_name=from_name,
                from_id=from_id,
                our_reply=our_reply,
                replied=replied,
                error=error,
                processed_at=datetime.utcnow()
            )
            session.merge(msg)
            session.commit()
            logger.debug(f"Marked message {message_id} as processed")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark message as processed: {e}")
        finally:
            session.close()
    
    def log_activity(self, activity_type: str, details: str = None):
        """Log bot activity."""
        session = get_db_session()
        try:
            import uuid
            activity = BotActivity(
                id=str(uuid.uuid4()),
                activity_type=activity_type,
                details=details,
                created_at=datetime.utcnow()
            )
            session.add(activity)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log activity: {e}")
        finally:
            session.close()
    
    def get_stats(self) -> dict:
        """Get bot statistics."""
        session = get_db_session()
        try:
            total_comments = session.query(ProcessedComment).count()
            replied_comments = session.query(ProcessedComment).filter_by(replied=True).count()
            total_messages = session.query(ProcessedMessage).count()
            replied_messages = session.query(ProcessedMessage).filter_by(replied=True).count()
            
            return {
                "total_comments_processed": total_comments,
                "comments_replied": replied_comments,
                "total_messages_processed": total_messages,
                "messages_replied": replied_messages,
            }
        finally:
            session.close()


# Singleton instance
db_manager = DatabaseManager()
