# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config
import logging


logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    Config.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=Config.DEBUG
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Base class for models
Base = declarative_base()

def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(engine)
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

def get_db():
    """Get database session (for dependency injection)"""
    db = Session()
    try:
        yield db
    finally:
        db.close()

def execute_sql_file(filepath):
    """Execute SQL file for initial setup"""
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
        
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = sql.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        
        logger.info(f"✓ SQL file executed: {filepath}")
        return True
    except Exception as e:
        logger.error(f"✗ SQL file execution failed: {e}")
        return False

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✓ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    @staticmethod
    def cleanup_old_data(days=90):
        """Clean up data older than specified days"""
        from datetime import datetime, timedelta
        from models import PhysiologicalData, WorkActivity, AIInteraction
        
        cutoff_date = datetime.now() - timedelta(days=days)
        db = Session()
        
        try:
            # Delete old physiological data
            deleted_physio = db.query(PhysiologicalData).filter(
                PhysiologicalData.timestamp < cutoff_date
            ).delete()
            
            # Delete old work activities
            deleted_work = db.query(WorkActivity).filter(
                WorkActivity.timestamp < cutoff_date
            ).delete()
            
            # Delete old AI interactions
            deleted_ai = db.query(AIInteraction).filter(
                AIInteraction.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"✓ Cleanup completed: {deleted_physio + deleted_work + deleted_ai} records deleted")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Cleanup failed: {e}")
            return False
        finally:
            db.close()

if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    if DatabaseManager.test_connection():
        print("✓ Database is ready!")
    else:
        print("✗ Database connection failed. Check your configuration.")