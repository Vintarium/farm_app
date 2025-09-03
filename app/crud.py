from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_farmer=user.is_farmer
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def create_product(db: Session, product: schemas.ProductCreate, user_id: int):
    db_product = models.Product(
        name=product.name, 
        description=product.description, 
        price=product.price, 
        image_url=product.image_url,
        owner_id=user_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_order(db: Session, order: schemas.OrderCreate, customer_id: int):
    db_order = models.Order(
        product_id=order.product_id,
        address=order.address,
        customer_id=customer_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order