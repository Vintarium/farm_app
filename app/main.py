from fastapi import FastAPI, Depends, Request, Form, HTTPException, status, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from pathlib import Path
import os
import uuid

from starlette.middleware.sessions import SessionMiddleware

from . import crud, models, schemas
from .database import SessionLocal, engine

# Создаём папки для хранения файлов, если они ещё не существуют
Path("static/images").mkdir(parents=True, exist_ok=True)
models.Base.metadata.create_all(bind=engine)

class FarmApp:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_middleware(SessionMiddleware, secret_key="ваш-очень-секретный-ключ")
        self.templates = Jinja2Templates(directory="app/templates")
        self.setup_routes()

    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def setup_routes(self):
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

        @self.app.get("/")
        def home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/register")
        def register_page(request: Request):
            return self.templates.TemplateResponse("register.html", {"request": request})

        @self.app.post("/register")
        def register_user(
            request: Request,
            db: Annotated[Session, Depends(self.get_db)],
            full_name: str = Form(...),
            email: str = Form(...),
            password: str = Form(...),
            is_farmer: Optional[str] = Form(None)
        ):
            db_user = crud.get_user_by_email(db, email=email)
            if db_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            is_farmer_value = is_farmer is not None

            user = schemas.UserCreate(
                full_name=full_name,
                email=email,
                password=password,
                is_farmer=is_farmer_value
            )
            
            crud.create_user(db=db, user=user)

            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        @self.app.get("/login")
        def login_page(request: Request):
            return self.templates.TemplateResponse("login.html", {"request": request})

        @self.app.post("/login")
        def login_user(
            request: Request,
            db: Annotated[Session, Depends(self.get_db)],
            email: str = Form(...),
            password: str = Form(...)
        ):
            user = crud.get_user_by_email(db, email=email)
            if not user or not crud.verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect email or password",
                )
            
            response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            request.session["user_id"] = user.id
            request.session["is_farmer"] = user.is_farmer
            return response

        @self.app.get("/logout")
        def logout_user(request: Request):
            request.session.clear()
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        @self.app.get("/products")
        def list_products(request: Request, db: Annotated[Session, Depends(self.get_db)]):
            products = crud.get_products(db)
            return self.templates.TemplateResponse("products.html", {"request": request, "products": products})

        # Маршруты для страницы фермера
        @self.app.get("/farmer")
        def farmer_page(request: Request, db: Annotated[Session, Depends(self.get_db)]):
            if not request.session.get("is_farmer"):
                return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

            user_id = request.session.get("user_id")
            products = db.query(models.Product).filter(models.Product.owner_id == user_id).all()
            return self.templates.TemplateResponse(
                "farmer.html", 
                {"request": request, "products": products}
            )
        
        @self.app.get("/add-product")
        def add_product_page(request: Request):
            if not request.session.get("is_farmer"):
                return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            return self.templates.TemplateResponse("add_product.html", {"request": request})

        @self.app.post("/add-product")
        async def add_product(
            request: Request,
            db: Annotated[Session, Depends(self.get_db)],
            name: str = Form(...),
            description: Optional[str] = Form(None),
            price: float = Form(...),
            image: UploadFile = File(None)
        ):
            if not request.session.get("is_farmer"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Доступ запрещен. Вы не являетесь фермером."
                )
            
            user_id = request.session.get("user_id")
            image_url = None
            if image and image.filename:
                # Создаем уникальное имя файла
                unique_filename = f"{uuid.uuid4()}_{image.filename}"
                file_path = Path("static/images") / unique_filename

                # Сохраняем файл
                file_path.write_bytes(await image.read())
                
                image_url = f"/static/images/{unique_filename}"

            product_data = schemas.ProductCreate(
                name=name,
                description=description,
                price=price,
                image_url=image_url
            )
            crud.create_product(db=db, product=product_data, user_id=user_id)
            return RedirectResponse(url="/farmer", status_code=status.HTTP_303_SEE_OTHER)

farm_app = FarmApp()
app = farm_app.app