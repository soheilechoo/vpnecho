from database.database import db
from database.models import Base, Product, BankCard, ProductPrice
from utils.logger import get_logger

logger = get_logger(__name__)

def run_migration():
    """اجرای مهاجرت دیتابیس"""
    try:
        # ایجاد جداول
        db.create_tables()
        logger.info("✅ Tables created successfully")
        
        with db.get_session() as session:
            # اضافه کردن محصولات پیش‌فرض
            default_products = [
                ("vip_single", "VPN VIP تک کاربره", 250),
                ("vip_dual", "VPN VIP دو کاربره", 450),
                ("normal_single", "VPN معمولی تک کاربره", 190),
                ("normal_dual", "VPN معمولی دو کاربره", 270)
            ]
            
            for product_type, name, price in default_products:
                existing = session.query(Product).filter_by(product_type=product_type).first()
                if not existing:
                    product = Product(
                        name=name,
                        product_type=product_type,
                        price=price
                    )
                    session.add(product)
                    logger.info(f"✅ Added product: {name}")
            
            # اضافه کردن قیمت‌های پیش‌فرض به ProductPrice
            for product_type, name, price in default_products:
                existing = session.query(ProductPrice).filter_by(product_type=product_type).first()
                if not existing:
                    price_record = ProductPrice(
                        product_type=product_type,
                        price=price
                    )
                    session.add(price_record)
            
            session.commit()
            
        logger.info("✅ Migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
