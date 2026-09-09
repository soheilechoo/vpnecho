# اضافه کردن به مدل‌های موجود

class BankCard(Base):
    __tablename__ = "bank_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String(16), unique=True, nullable=False, index=True)
    card_holder_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductPrice(Base):
    __tablename__ = "product_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String(50), unique=True, nullable=False, index=True)  # vip_single, vip_dual, normal_single, normal_dual
    price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
