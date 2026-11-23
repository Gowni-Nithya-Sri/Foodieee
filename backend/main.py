
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from typing import List, Literal

from database import engine, Base, get_db
import models


app = FastAPI(title="Foodie API")


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables
Base.metadata.create_all(bind=engine)


# Add new columns to existing SQLite tables.
# create_all() does not automatically update existing tables.
def migrate_database():
    inspector = inspect(engine)

    migrations = {
        "orders": {
            "customer_name": "VARCHAR",
            "phone": "VARCHAR",
            "delivery_address": "VARCHAR",
            "restaurant_name": "VARCHAR",
            "payment_method": "VARCHAR",
            "delivery_fee": "FLOAT DEFAULT 30.0"
        },
        "order_items": {
            "food_name": "VARCHAR",
            "unit_price": "FLOAT"
        }
    }

    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )


migrate_database()


# Registration request model
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""


# Checkout item model
class OrderItemCreate(BaseModel):
    name: str
    price: float = Field(gt=0)
    quantity: int = Field(ge=1)


# Checkout request model
class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    delivery_address: str
    restaurant_name: str
    payment_method: Literal["Cash on Delivery"]
    delivery_fee: float = Field(default=30.0, ge=0)
    items: List[OrderItemCreate] = Field(min_length=1)


@app.get("/")
def home():
    return {"message": "Welcome to Foodie!"}


# Register user
@app.post("/users")
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = models.User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "name": user.name
    }


# Get registered users
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# Place an order
@app.post("/orders")
def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        subtotal = sum(
            item.price * item.quantity
            for item in order_data.items
        )

        total = subtotal + order_data.delivery_fee

        new_order = models.Order(
            customer_name=order_data.customer_name,
            phone=order_data.phone,
            delivery_address=order_data.delivery_address,
            restaurant_name=order_data.restaurant_name,
            payment_method=order_data.payment_method,
            delivery_fee=order_data.delivery_fee,
            total_amount=total,
            status="Placed"
        )

        db.add(new_order)
        db.flush()

        for item in order_data.items:
            order_item = models.OrderItem(
                order_id=new_order.id,
                food_name=item.name,
                unit_price=item.price,
                quantity=item.quantity
            )

            db.add(order_item)

        db.commit()
        db.refresh(new_order)

        return {
            "message": "Order placed successfully!",
            "order_id": new_order.id,
            "customer_name": new_order.customer_name,
            "restaurant_name": new_order.restaurant_name,
            "total_amount": round(total, 2),
            "status": new_order.status
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to place order. Please try again."
        )


# Get a particular order
@app.get("/orders/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order_id
    ).all()

    return {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "delivery_address": order.delivery_address,
        "restaurant_name": order.restaurant_name,
        "payment_method": order.payment_method,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": [
            {
                "name": item.food_name,
                "price": item.unit_price,
                "quantity": item.quantity
            }
            for item in items
        ]
    }
