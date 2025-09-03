from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_farmer: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    owner_id: int
    created_at: datetime
    owner: User

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    product_id: int
    address: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    customer_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True