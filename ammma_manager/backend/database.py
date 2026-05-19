from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Caminho para o banco de dados na pasta data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Se estiver no Railway/Render, usa a pasta do próprio backend para o SQLite para evitar erros de permissão fora da pasta /app
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
    DB_PATH = os.path.join(BASE_DIR, "database.db")
else:
    DB_PATH = os.path.join(BASE_DIR, "..", "data", "database.db")

# Suporta banco de dados na nuvem (PostgreSQL, etc.) via variável de ambiente, senão usa SQLite local
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if SQLALCHEMY_DATABASE_URL:
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Garante que a pasta pai do DB_PATH existe
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1) # 1 = Ativo, 0 = Inativo
    role = Column(String, default="colaborador") # admin ou colaborador

class Config(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True) # filament_price, hour_price, owner_name, etc.
    value = Column(Float, nullable=True)
    string_value = Column(String, nullable=True)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    orders = relationship("Order", back_populates="client")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String)
    weight_g = Column(Float)
    time_hours = Column(Float)
    final_cost = Column(Float)
    suggested_price = Column(Float)
    original_price = Column(Float, nullable=True)
    discount_amount = Column(Float, default=0.0)
    notes = Column(String, nullable=True)
    status = Column(String, default="Orçamento") # Orçamento, Aprovado, Fila, Imprimindo, Pronto
    client_name = Column(String, default="Consumidor Final")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", back_populates="orders")
    
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=True)
    printer = relationship("Printer", back_populates="orders")
    
    delivery_date = Column(DateTime, nullable=True)
    
    # Novos campos para gestão financeira
    paid_amount = Column(Float, default=0.0)
    payment_status = Column(String, default="Pendente") # Pendente, Parcial, Pago

class Printer(Base):
    __tablename__ = "printers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    model = Column(String)
    status = Column(String, default="Disponível") # Disponível, Manutenção, Ocupada
    total_hours = Column(Float, default=0.0)
    maintenance_alert_hours = Column(Float, default=500.0)
    orders = relationship("Order", back_populates="printer")

class FailureLog(Base):
    __tablename__ = "failures"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    weight_wasted_g = Column(Float)
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class FixedExpense(Base):
    __tablename__ = "fixed_expenses"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    value = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

class ProjectGallery(Base):
    __tablename__ = "gallery"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    image_path = Column(String)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String) # Ex: PLA, PETG
    color = Column(String) # Ex: Preto, Branco
    brand = Column(String, nullable=True) # Ex: 3D Lab, Creality
    weight_g = Column(Float) # Peso atual ou Quantidade
    min_weight_g = Column(Float, default=100.0) # Alerta de estoque baixo
    price_paid = Column(Float, nullable=True) # Preço pago pelo item
    initial_amount = Column(Float) # Quantidade original comprada
    category = Column(String, default="Filamento") # Filamento, Embalagem, Insumos
    unit = Column(String, default="g") # g, un, m
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Discount(Base):
    __tablename__ = "discounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    type = Column(String) # 'percentage' ou 'fixed'
    value = Column(Float)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class CatalogItem(Base):
    __tablename__ = "catalog"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    image_path = Column(String)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import create_engine

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency para o FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
