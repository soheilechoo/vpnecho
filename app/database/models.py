class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="orders")
    product = relationship("Product")

    __table_args__ = (
        Index('ix_orders_user_id_status', 'user_id', 'status'),
        Index('ix_orders_order_number', 'order_number'),
    )

    def __repr__(self):
        return f"<Order {self.order_number}: {self.status}>"
