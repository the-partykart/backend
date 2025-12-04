import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import DECIMAL, TIMESTAMP, BigInteger, Column, Integer, Numeric, String, ForeignKey, DateTime, Boolean, JSON, Text, create_engine
from sqlalchemy.sql import func 
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker

from config.config import settings


Base = declarative_base()


class Users(Base):
    __tablename__ = "pk_users"

    user_id = Column(Integer, primary_key=True, index=True)
    phone_no = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=True, index=True)
    business_name = Column(String(100), nullable=True, index=True)
    email = Column(String(70), unique=True, nullable=True, index=True)
    password = Column(String(400), nullable=False)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey('pk_users.user_id'), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, ForeignKey('pk_users.user_id'), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user_role = relationship("UserRoles", back_populates="user")


class Roles(Base):
    __tablename__ = "pk_roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False, index=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user_role = relationship("UserRoles", back_populates="role")


class UserRoles(Base):
    __tablename__ = "pk_user_roles"

    user_role_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("pk_users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("pk_roles.role_id"), nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("Users", back_populates="user_role")
    role = relationship("Roles", back_populates="user_role")

# class Products(Base):
#     __tablename__ = "pk_products"

#     product_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     product_name = Column(String(100), nullable=False)
#     product_price = Column(Integer, primary_key=True, index=True)
#     product_description = Column(Text(2000), nullable=True)
#     product_image = Column(JSON, nullable=True)
#     sub_category_id = Column(Integer, nullable=True)
#     created_by = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=func.now(), nullable=False)
#     updated_by = Column(Integer, nullable=True)
#     updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     deleted_by = Column(Integer, nullable=True)
#     deleted_at = Column(DateTime, nullable=True)

class Products(Base):
    __tablename__ = "pk_products"

    product_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_name = Column(String(100), nullable=False, index=True)
    product_price = Column(Integer, nullable=False)
    product_full_price = Column(Integer, nullable=True, default=None)
    product_description = Column(Text(2000), nullable=True)
    product_image = Column(JSON, nullable=True)
    sub_category_id = Column(Integer, ForeignKey("pk_sub_category.sub_category_id"), nullable=True, index=True)
    stock = Column(Integer, nullable= True)

    # --- Shipping & Delivery fields ---
    weight = Column(DECIMAL(10, 2), nullable=True, comment="Weight in kilograms")
    length = Column(DECIMAL(10, 2), nullable=True, comment="Length in centimeters")
    width = Column(DECIMAL(10, 2), nullable=True, comment="Width in centimeters")
    height = Column(DECIMAL(10, 2), nullable=True, comment="Height in centimeters")
    volumetric_weight = Column(DECIMAL(10, 2), nullable=True, comment="Volumetric weight (L*W*H/5000)")
    dimensional_factor = Column(DECIMAL(10, 2), default=5000.00, nullable=False, comment="Factor for volumetric calc")
    origin_location = Column(String(255), nullable=True, comment="Origin city or warehouse address")

    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # --- Relationships ---
    sub_category = relationship("SubCategary", backref="products")
    order_items = relationship("OrderItem", back_populates="product")


    # --- Utility Method ---
    def calculate_volumetric_weight(self):
        """Safely calculate volumetric weight (L×W×H / 5000)."""
        try:
            if self.length and self.width and self.height:
                self.volumetric_weight = round(
                    (self.length * self.width * self.height) / 5000, 2
                )
            else:
                self.volumetric_weight = None
        except Exception as e:
            self.volumetric_weight = None




class Categary(Base):
    __tablename__ = "pk_category"

    category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    category_image = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class SubCategary(Base):
    __tablename__ = "pk_sub_category"

    sub_category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sub_category_name = Column(String(100), nullable=False, index=True)
    sub_category_image = Column(String(500), nullable=True)
    category_id = Column(Integer, nullable=False, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class CategaryMapping(Base):
    __tablename__ = "pk_category_mapping"

    category_mapping_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id = Column(Integer, nullable=False, index=True)
    sub_category_id = Column(Integer, nullable=False, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)



class Offers(Base):
    __tablename__ = "pk_offers"

    offer_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    offer_name = Column(String(100), nullable=False)
    offer_percentage = Column(Integer, primary_key=True)
    offer_description = Column(Text(2000), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class Promocodes(Base):
    __tablename__ = "pk_promocode"

    promocode_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    promocode_name = Column(String(100), nullable=False)
    promocode_percentage = Column(Integer, primary_key=True)
    promocode_description = Column(Text(2000), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class Log(Base):
    __tablename__ = "pk_log"
    log_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    log_name = Column(String(255), nullable=False)
    log_description = Column(Text(1000), nullable=True)
    previous_value = Column(Text(2000), nullable= True)
    updated_value = Column(Text(2000),nullable= True)
    changed_by = Column(Integer, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=func.now())


class BuyProducts(Base):
    __tablename__ = "pk_buy_products"

    buy_product_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(BigInteger,nullable=False)
    product_id = Column(String(100), nullable=False)
    product_price = Column(Integer, nullable=True)
    category_id = Column(Integer, nullable=True)
    sub_category_id = Column(Integer, nullable=True)
    shipping_address = Column(JSON, nullable=True)
    payment_method = Column(String(100), nullable=True)
    payment_status = Column(String(100), nullable=True, default=0)
    quantity = Column(Integer, nullable=True)
    offer_id = Column(Integer, nullable=True)
    offer_percentage = Column(Integer, nullable=True)
    promocode_id = Column(Integer, nullable= True)
    promocode_amount = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_canceled = Column(Boolean, default=False, nullable=False)
    canceled_by = Column(Integer, nullable=True)
    canceled_at = Column(DateTime, nullable=True)


# class OrderAlert(Base):
#     __tablename__ = "pk_order_alert"

#     order_alert_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     buy_product_id = Column(Integer, nullable=False)
#     order_id = Column(BigInteger, nullable=False)
#     total_amount = Column(BigInteger, nullable=False)
#     delivery_status = Column(String(100), nullable=False)
#     created_by = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=func.now(), nullable=False)
#     updated_by = Column(Integer, nullable=True)
#     updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
#     is_canceled = Column(Boolean, default=False, nullable=False)
#     canceled_by = Column(Integer, nullable=True)
#     canceled_at = Column(DateTime, nullable=True)



class Cart(Base):
    __tablename__ = "pk_cart"

    cart_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_canceled = Column(Boolean, default=False, nullable=False)
    canceled_by = Column(Integer, nullable=True)
    canceled_at = Column(DateTime, nullable=True)


class Information(Base):
    __tablename__ = "pk_information"

    information_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    information_name = Column(String(100), nullable=False)
    information_description = Column(JSON, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class DashBoardImage(Base):
    __tablename__ = "pk_dashboard_image"

    dashboard_image_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dashboard_image_link = Column(String(300), nullable=False)
    dashboard_image_order = Column(JSON, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)



###----------------------------------------------------------------------



# 2️⃣ Orders (placed by user)
class Order(Base):
    __tablename__ = "pk_orders"

    order_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), nullable=False, default=0)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), default="Pending")
    delivery_status = Column(String(50), default="Pending")
    delivery_tracking_id = Column(String(100))
    shipping_address = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete")
    alerts = relationship("OrderAlert", back_populates="order", cascade="all, delete")


# 3️⃣ Order Items (each product line inside an order)
class OrderItem(Base):
    __tablename__ = "pk_order_items"

    order_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("pk_orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("pk_products.product_id", ondelete="RESTRICT"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    offer_id = Column(Integer, nullable=True)
    promocode_id = Column(Integer, nullable=True)
    offer_discount = Column(DECIMAL(10, 2), nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Products", back_populates="order_items", lazy="joined")



# 4️⃣ Order Alerts (status changes, delivery updates, etc.)
class OrderAlert(Base):
    __tablename__ = "pk_order_alerts"

    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("pk_orders.order_id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    alert_message = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship
    order = relationship("Order", back_populates="alerts")


class BigShipToken(Base):
    __tablename__ = "bigship_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class OrderShipment(Base):
    __tablename__ = "pk_order_shipments"

    shipment_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    order_id = Column(BigInteger, ForeignKey("pk_orders.order_id", ondelete="CASCADE"))
    order = relationship("Order", backref="shipment")

    # Packing details (admin will update these)
    shipment_weight = Column(DECIMAL(10,2), nullable=True)
    shipment_length = Column(DECIMAL(10,2), nullable=True)
    shipment_width = Column(DECIMAL(10,2), nullable=True)
    shipment_height = Column(DECIMAL(10,2), nullable=True)
    shipment_chargeable_weight = Column(DECIMAL(10,2), nullable=True)

    # BigShip response details
    bigship_system_order_id = Column(String(255), nullable=True)
    bigship_master_awb = Column(String(255), nullable=True)
    bigship_courier_id = Column(Integer, nullable=True)
    bigship_label_base64 = Column(Text, nullable=True)

    manifest_status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())



# class Courses(Base):
#     __tablename__ = "pk_courses"

#     course_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     course_name = Column(String(300), nullable=False)
#     course_link = Column(String(300), nullable=False)
#     course_subcategory = Column(Integer, nullable=False)
#     created_by = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=func.now(), nullable=False)
#     updated_by = Column(Integer, nullable=True)
#     updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     canceled_by = Column(Integer, nullable=True)
#     canceled_at = Column(DateTime, nullable=True)


# class CourseCategary(Base):
#     __tablename__ = "pk_category"

#     category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     category_name = Column(String(100), nullable=False, index=True)
#     category_image = Column(String(500), nullable=True)
#     created_by = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=func.now(), nullable=False)
#     updated_by = Column(Integer, nullable=True)
#     updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     deleted_by = Column(Integer, nullable=True)
#     deleted_at = Column(DateTime, nullable=True)


# class CourseSubCategary(Base):
#     __tablename__ = "pk_sub_category"

#     sub_category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     sub_category_name = Column(String(100), nullable=False, index=True)
#     sub_category_image = Column(String(500), nullable=True)
#     category_id = Column(Integer, nullable=False, index=True)
#     created_by = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=func.now(), nullable=False)
#     updated_by = Column(Integer, nullable=True)
#     updated_at = Column(DateTime, onupdate=func.now(),nullable=True)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     deleted_by = Column(Integer, nullable=True)
#     deleted_at = Column(DateTime, nullable=True)




# Note: if your project already defines these models, remove duplicates and only keep routes/schemas.
class CourseCategory(Base):
    __tablename__ = "pk_course_category"

    category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    category_image = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    subcategories = relationship("CourseSubCategory", back_populates="category", lazy="selectin")


class CourseSubCategory(Base):
    __tablename__ = "pk_course_sub_category"

    sub_category_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sub_category_name = Column(String(100), nullable=False, index=True)
    sub_category_image = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey("pk_course_category.category_id"), nullable=False, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    category = relationship("CourseCategory", back_populates="subcategories")
    courses = relationship("Courses", back_populates="subcategory", lazy="selectin")


class Courses(Base):
    __tablename__ = "pk_courses"

    course_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_name = Column(String(300), nullable=False)
    course_link = Column(String(300), nullable=False)
    course_subcategory = Column(
        Integer,
        ForeignKey("pk_course_sub_category.sub_category_id"),
        nullable=False,
        index=True,
    )
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    canceled_by = Column(Integer, nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    subcategory = relationship("CourseSubCategory", back_populates="courses")


### ------------------------------------------------------------------ 

from app.db.db_session import *

async def async_create_tables(async_engine):
    # Base.metadata.create_all(async_engine)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def async_remove_tables(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def main(operation):
    if operation == 1:
        await async_create_tables(async_engine)
        print("Table create successfully")
        
    elif operation == 0:
        await async_remove_tables(async_engine)
        print("all table removed sucessfully")


db_name = settings.db_name
db_drivername = settings.db_drivername
db_username = settings.db_username
db_password = settings.db_password
db_port = settings.db_port
db_database_name = settings.db_database_name
db_server = settings.db_server

# engine = create_engine(f"{db_name}+{db_drivername}://{db_username}:{db_password}@{db_server}:{db_port}/{db_database_name}")

DB_url = f"mysql+asyncmy://{db_username}:{quote_plus(db_password)}@{db_server}:{db_port}/{db_database_name}"


if __name__ == "__main__":
    # async_engine = create_async_engine((f"{db_name}+{db_drivername}://{db_username}:{db_password}@{db_server}:{db_port}/{db_database_name}"))
    # create_tables(async_engine=async_engine)  
    asyncio.run(main(1))




