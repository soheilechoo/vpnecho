from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

# بارگذاری متغیرهای محیطی
from dotenv import load_dotenv
load_dotenv()

# دریافت آدرس دیتابیس از محیط
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./echo_vpn.db')

# ایجاد موتور دیتابیس
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# ایجاد سشن فکتوری
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ایجاد بیس برای مدل‌ها
Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """ایجاد جداول در دیتابیس"""
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """دریافت سشن دیتابیس"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# نمونه از دیتابیس
db = Database()
