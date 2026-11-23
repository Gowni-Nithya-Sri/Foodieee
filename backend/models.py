
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    price = Column(Float, nullable=False)
    image = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    delivery_address = Column(String, nullable=True)
    restaurant_name = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)

    total_amount = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=30.0)
    status = Column(String, default="Placed")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))

    # Keep the original food_id column for compatibility
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)

    food_name = Column(String, nullable=True)
    unit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
