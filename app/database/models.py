from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import enum

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    REJECTED = "rejected"

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    balance = Column(Float, default=0.0)
    successful_transactions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    payments = relationship("Payment", back_populates="user")
    wallet_transactions = relationship("WalletTransaction", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    receipt_file_id = Column(String(200), nullable=True)
    receipt_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    admin_id = Column(BigInteger, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    __table_args__ = (
        Index('ix_payments_user_id_status', 'user_id', 'status'),
        Index('ix_payments_transaction_id', 'transaction_id'),
    )

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    reference_id = Column(String(100), nullable=True)
    status = Column(String(20), default="success")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="wallet_transactions")
    
    __table_args__ = (
        Index('ix_wallet_transactions_user_id_type', 'user_id', 'type'),
    )

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    product = relationship("Product")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    product_type = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
