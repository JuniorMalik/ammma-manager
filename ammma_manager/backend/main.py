from database import init_db, get_db, Order, Client, User, Config, Inventory, Discount, Printer, FailureLog, ProjectGallery, FixedExpense
from auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

from calculator import CostCalculator, PrintSettings
from pdf_export import generate_pdf_budget
import shutil
from jose import jwt, JWTError

# Inicializar o banco de dados
init_db()

# Garantir usuário admin padrão
db = next(get_db())
if not db.query(User).filter(User.username == "admin").first():
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("AM3D@MGR#1"),
        role="DEV"
    )
    db.add(admin_user)

# Garantir configurações padrão (Numéricas e Texto)
default_configs_data = {
    "filament_price_kg": 120.0,
    "hour_machine_price": 1.50,
    "hour_work_price": 15.0,
    "owner_name": "Mayara Perez",
    "owner_role": "Gerente Comercial",
    "owner_phone": "(11) 9 7355 9491",
    "pix_key": "11973559491"
}

for k, v in default_configs_data.items():
    if not db.query(Config).filter(Config.key == k).first():
        if isinstance(v, (int, float)):
            db.add(Config(key=k, value=float(v)))
        else:
            db.add(Config(key=k, string_value=v))

db.commit()
db.close()

app = FastAPI(title="AMMMA 3D Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Se estiver no Railway/Render, o frontend está na Hostinger, então criamos pastas dummy dentro de /app para evitar RuntimeError ou PermissionError
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
    frontend_path = os.path.join(BASE_DIR, "dummy_frontend")
    logo_path = os.path.join(BASE_DIR, "logo")
else:
    frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
    logo_path = os.path.abspath(os.path.join(frontend_path, "logo"))

upload_path = os.path.abspath(os.path.join(BASE_DIR, "uploads"))

# Garante que os diretórios existem antes de montar
os.makedirs(frontend_path, exist_ok=True)
os.makedirs(logo_path, exist_ok=True)
os.makedirs(upload_path, exist_ok=True)

app.mount("/static", StaticFiles(directory=frontend_path), name="static")
app.mount("/logo", StaticFiles(directory=logo_path), name="logo")
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

# --- AUTENTICAÇÃO E SEGURANÇA ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

def get_current_user(request: Request, db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)):
    # Tenta pegar do header Bearer ou da Query String (?token=... para PDFs)
    actual_token = token
    if not actual_token and request:
        actual_token = request.query_params.get("token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not actual_token:
        raise credentials_exception

    try:
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def check_admin(user: User = Depends(get_current_user)):
    if user.role != "admin" and user.role != "DEV":
        raise HTTPException(status_code=403, detail="Acesso negado: Requer privilégios de administrador")
    return user

# Rota para servir o index.html na raiz
@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/login")
def read_login():
    return FileResponse(os.path.join(frontend_path, "login.html"))

@app.get("/sw.js")
def read_sw():
    return FileResponse(os.path.join(frontend_path, "sw.js"))

@app.get("/manifest.json")
def read_manifest():
    return FileResponse(os.path.join(frontend_path, "manifest.json"))

# --- GERADOR DE PDF ---

@app.get("/orders/{order_id}/pdf")
@app.get("/orders/{order_id}/pdf_pro")
def generate_order_pdf(order_id: int, gallery_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order: raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Carregar contatos das configs
    configs = {c.key: (c.value if c.value is not None else c.string_value) for c in db.query(Config).all()}
    contacts = {
        "owner_name": configs.get("owner_name", "Mayara Perez"),
        "owner_role": configs.get("owner_role", "Gerente Comercial"),
        "owner_phone": configs.get("owner_phone", "(11) 9 7355 9491"),
        "pix_key": configs.get("pix_key", "11973559491")
    }

    client = order.client
    gallery_item = None
    if gallery_id:
        gallery_item = db.query(ProjectGallery).filter(ProjectGallery.id == gallery_id).first()
        
    pdf_content = generate_pdf_budget(order, client, gallery_item, logo_path, upload_path, contacts=contacts)
    
    return Response(content=pdf_content, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=Orcamento_AMMMA3D_{order.id}.pdf"
    })

# Configuração de CORS para permitir que o frontend acesse o backend
# Removido middleware redundante que estava aqui.

@app.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Pedidos por status
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "Orçamento").count()
    production_orders = db.query(Order).filter(Order.status.in_(["Aprovado", "Fila", "Imprimindo"])).count()
    finished_orders = db.query(Order).filter(Order.status == "Pronto").all()
    
    # Peso total usado em pedidos concluídos
    total_weight_g = sum(o.weight_g for o in finished_orders)
    
    # Preço médio do filamento para cálculo de desperdício
    configs = {c.key: c.value for c in db.query(Config).all()}
    fil_price_kg = configs.get("filament_price_kg", 120.0)
    
    # Cálculo de Falhas (Desperdício)
    failures = db.query(FailureLog).all()
    total_wasted_g = sum(f.weight_wasted_g for f in failures)
    total_wasted_cost = (total_wasted_g / 1000) * fil_price_kg

    # Financeiro de pedidos concluídos (Vendas Reais)
    total_cost_finished = sum(o.final_cost for o in finished_orders)
    total_revenue_finished = sum(o.suggested_price for o in finished_orders)
    
    # Lucro Líquido Real (Receita - Custo - Desperdício - Despesas Fixas)
    expenses = db.query(FixedExpense).all()
    total_expenses = sum(e.value for e in expenses)
    net_profit = total_revenue_finished - total_cost_finished - total_wasted_cost - total_expenses

    # Valor Total do Inventário (Patrimônio) e Alertas de Estoque Baixo
    inventory_items = db.query(Inventory).all()
    inventory_value = 0
    low_stock_items = []
    for item in inventory_items:
        if item.price_paid and item.initial_amount and item.initial_amount > 0:
            unit_price = item.price_paid / item.initial_amount
            inventory_value += unit_price * item.weight_g
        
        # Alerta de estoque baixo
        if item.weight_g <= item.min_weight_g:
            low_stock_items.append({
                "name": f"{item.material_name} {item.color}",
                "current": item.weight_g,
                "unit": item.unit
            })
    
    # Margem Média
    avg_margin = 0
    if finished_orders:
        margins = [(o.suggested_price - o.final_cost) / o.suggested_price for o in finished_orders if o.suggested_price > 0]
        if margins:
            avg_margin = sum(margins) / len(margins) * 100

    # Top 3 Projetos
    top_projects_query = db.query(Order.project_name, func.count(Order.id).label('total'))\
        .filter(Order.status == "Pronto")\
        .group_by(Order.project_name)\
        .order_by(func.count(Order.id).desc())\
        .limit(3).all()
    top_projects = [{"name": p[0], "count": p[1]} for p in top_projects_query]

    # Tempo Médio de Produção (Lead Time) em horas
    avg_lead_time = 0
    finished_with_dates = [o for o in finished_orders if o.finished_at and o.created_at]
    if finished_with_dates:
        lead_times = [(o.finished_at - o.created_at).total_seconds() / 3600 for o in finished_with_dates]
        avg_lead_time = sum(lead_times) / len(lead_times)

    # Evolução de Vendas (Últimos 6 meses)
    sales_evo_query = db.query(
        func.strftime('%Y-%m', Order.created_at).label('month'),
        func.sum(Order.suggested_price).label('revenue'),
        func.sum(Order.final_cost).label('cost')
    ).filter(Order.status == "Pronto")\
     .group_by('month')\
     .order_by('month')\
     .limit(6).all()
    
    sales_evolution = [{"month": s[0], "revenue": round(s[1], 2), "cost": round(s[2], 2)} for s in sales_evo_query]

    # Status das Impressoras
    printers = db.query(Printer).all()
    printer_summary = {
        "total": len(printers),
        "busy": len([p for p in printers if p.status == "Ocupada"]),
        "maintenance": len([p for p in printers if p.status == "Manutenção"]),
        "idle": len([p for p in printers if p.status == "Disponível"]),
        "needing_maintenance": [p.name for p in printers if p.total_hours >= p.maintenance_alert_hours]
    }

    # Atividades Recentes (Últimos 5 pedidos ou falhas)
    recent_orders = db.query(Order).order_by(desc(Order.created_at)).limit(5).all()
    activities = []
    for o in recent_orders:
        activities.append({
            "type": "order",
            "msg": f"Novo pedido: {o.project_name} para {o.client_name}",
            "time": o.created_at,
            "status": o.status
        })
    
    recent_failures = db.query(FailureLog).order_by(desc(FailureLog.created_at)).limit(3).all()
    for f in recent_failures:
        activities.append({
            "type": "failure",
            "msg": f"Falha registrada: {f.weight_wasted_g}g - {f.reason}",
            "time": f.created_at,
            "status": "Erro"
        })
    
    activities.sort(key=lambda x: x["time"], reverse=True)

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "production_orders": production_orders,
        "finished_count": len(finished_orders),
        "total_weight_kg": round(total_weight_g / 1000, 2),
        "total_wasted_kg": round(total_wasted_g / 1000, 2),
        "total_wasted_cost": round(total_wasted_cost, 2),
        "inventory_value": round(inventory_value, 2),
        "total_cost": round(total_cost_finished, 2),
        "total_revenue": round(total_revenue_finished, 2),
        "net_profit": round(net_profit, 2),
        "low_stock_items": low_stock_items,
        "avg_margin": round(avg_margin, 2),
        "top_projects": top_projects,
        "avg_lead_time": round(avg_lead_time, 1),
        "sales_evolution": sales_evolution,
        "printer_summary": printer_summary,
        "recent_activities": activities[:5]
    }

# --- CONFIGURAÇÕES DINÂMICAS ---

@app.get("/configs")
def get_configs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    configs = db.query(Config).all()
    return {c.key: (c.value if c.value is not None else c.string_value) for c in configs}

class ConfigUpdate(BaseModel):
    key: str
    value: Optional[float] = None
    string_value: Optional[str] = None

@app.patch("/configs")
def update_configs(data: List[ConfigUpdate], db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    for item in data:
        config = db.query(Config).filter(Config.key == item.key).first()
        if not config:
            config = Config(key=item.key, value=item.value, string_value=item.string_value)
            db.add(config)
        else:
            if item.value is not None: config.value = item.value
            if item.string_value is not None: config.string_value = item.string_value
    db.commit()
    return {"message": "Configurações atualizadas com sucesso"}

# --- CALCULADORA ---

class CalcRequest(BaseModel):
    weight_g: float
    time_hours: float
    labor_hours: float = 0
    consumables: float = 0
    packaging: float = 0
    coupon_code: str = None
    markup_percent: float = 100.0

@app.post("/calculate")
def calculate_costs(data: CalcRequest, db: Session = Depends(get_db)):
    print(f"Calculando para: {data}")
    configs_list = db.query(Config).all()
    configs = {c.key: (c.value if c.value is not None else c.string_value) for c in configs_list}
    
    # markup_factor = 1 + (markup_percent / 100)
    markup_factor = 1.0 + (data.markup_percent / 100.0)
    
    # Configurar as definições de preço
    settings = PrintSettings(
        filament_price_kg=configs.get("filament_price_kg", 120.0),
        electricity_cost_h=0.11, # Pode vir do config também
        printer_depreciation_h=0.58,
        labor_rate_h=configs.get("hour_work_price", 15.0),
        markup_factor=markup_factor
    )
    
    calculator = CostCalculator(settings)
    result = calculator.calculate(
        weight_g=data.weight_g,
        time_hours=data.time_hours,
        labor_hours=data.labor_hours,
        consumables=data.consumables,
        packaging=data.packaging
    )
    
    suggested_sale = result["suggested_sale"]
    discount_amount = 0
    if data.coupon_code:
        coupon = db.query(Discount).filter(Discount.code == data.coupon_code.upper(), Discount.is_active == 1).first()
        if coupon:
            if coupon.type == 'percentage':
                discount_amount = suggested_sale * (coupon.value / 100)
            else:
                discount_amount = coupon.value
            suggested_sale -= discount_amount

    return {
        "final_cost": result["final_cost"],
        "suggested_sale": round(max(suggested_sale, result["final_cost"]), 2),
        "discount_applied": round(discount_amount, 2),
        "weight_g": data.weight_g,
        "time_hours": data.time_hours,
        "details": result # Enviando detalhes extras para o frontend se quiser mostrar
    }

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha incorretos")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    return db.query(User).all()

@app.post("/users")
def create_user(data: dict, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    if db.query(User).filter(User.username == data["username"]).first():
        raise HTTPException(status_code=400, detail="Usuário já existe")
    new_user = User(username=data["username"], hashed_password=get_password_hash(data["password"]), role=data["role"])
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.patch("/users/{username}/status")
def toggle_user_status(username: str, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    if username == "admin":
        raise HTTPException(status_code=400, detail="Não é possível desativar o admin principal")
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="Você não pode desativar sua própria conta")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.is_active = 0 if user.is_active else 1
    db.commit()
    return {"message": f"Usuário {username} atualizado", "is_active": user.is_active}

@app.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    if username == "admin":
        raise HTTPException(status_code=400, detail="Não é possível deletar o admin principal")
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="Você não pode deletar sua própria conta")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(user)
    db.commit()
    return {"message": "Usuário deletado"}

class PasswordReset(BaseModel):
    new_password: str

@app.patch("/users/{username}/role")
def change_user_role(username: str, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    if username == "admin":
        raise HTTPException(status_code=400, detail="O cargo do admin não pode ser alterado")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.role = "admin" if user.role == "colaborador" else "colaborador"
    db.commit()
    return {"message": "Cargo alterado", "role": user.role}

@app.patch("/users/{username}/password")
def reset_password(username: str, data: PasswordReset, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    if username == "admin":
        raise HTTPException(status_code=400, detail="Use o script de terminal para resetar a senha do admin")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Senha atualizada"}

# --- GESTÃO DE IMPRESSORAS ---

class PrinterCreate(BaseModel):
    name: str
    model: str
    maintenance_alert_hours: float = 500.0

@app.get("/printers")
def list_printers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Printer).all()

@app.post("/printers")
def create_printer(data: PrinterCreate, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    new_printer = Printer(**data.dict())
    db.add(new_printer)
    db.commit()
    db.refresh(new_printer)
    return new_printer

@app.patch("/printers/{printer_id}/status")
def update_printer_status(printer_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer: raise HTTPException(status_code=404, detail="Impressora não encontrada")
    if "status" in data: printer.status = data["status"]
    if "add_hours" in data: printer.total_hours += data["add_hours"]
    db.commit()
    return printer

@app.delete("/printers/{printer_id}")
def delete_printer(printer_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    db.delete(printer)
    db.commit()
    return {"message": "Impressora removida"}

# --- GESTÃO DE FALHAS ---

class FailureCreate(BaseModel):
    order_id: Optional[int] = None
    weight_wasted_g: float
    reason: str

@app.get("/failures")
def list_failures(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FailureLog).order_by(desc(FailureLog.created_at)).all()

@app.post("/failures")
def create_failure(data: FailureCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_failure = FailureLog(**data.dict())
    db.add(new_failure)
    db.commit()
    db.refresh(new_failure)
    return new_failure

# --- GESTÃO DE CLIENTES ---

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

@app.get("/clients")
def list_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Client).all()

@app.post("/clients")
def create_client(data: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_client = Client(**data.dict())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client: raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
    return {"message": "Cliente removido"}

# --- GESTÃO DE DESPESAS FIXAS ---

class ExpenseCreate(BaseModel):
    description: str
    value: float

@app.get("/expenses")
def list_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FixedExpense).order_by(desc(FixedExpense.date)).all()

@app.post("/expenses")
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    new_expense = FixedExpense(**data.dict())
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    expense = db.query(FixedExpense).filter(FixedExpense.id == expense_id).first()
    if not expense: raise HTTPException(status_code=404, detail="Despesa não encontrada")
    db.delete(expense)
    db.commit()
    return {"message": "Despesa removida"}

# --- GALERIA DE PROJETOS ---

from fastapi import UploadFile, File, Form

@app.get("/gallery")
def list_gallery(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ProjectGallery).order_by(desc(ProjectGallery.created_at)).all()

@app.post("/gallery")
async def add_to_gallery(
    project_name: str = Form(...),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file_path = os.path.join(upload_path, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    new_entry = ProjectGallery(
        project_name=project_name,
        image_path=f"/uploads/{filename}",
        notes=notes
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

@app.delete("/gallery/{entry_id}")
def delete_gallery_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    entry = db.query(ProjectGallery).filter(ProjectGallery.id == entry_id).first()
    if not entry: raise HTTPException(status_code=404, detail="Entrada não encontrada")
    
    # Remover arquivo físico
    filename = os.path.basename(entry.image_path)
    file_path = os.path.join(upload_path, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.delete(entry)
    db.commit()
    return {"message": "Entrada removida"}

# --- ROTAS DE PEDIDOS ---

class OrderCreate(BaseModel):
    project_name: str
    client_name: str = "Consumidor Final"
    client_id: Optional[int] = None
    delivery_date: Optional[str] = None
    weight_g: float
    time_hours: float
    final_cost: float
    suggested_price: float
    original_price: Optional[float] = None
    discount_amount: float = 0.0
    notes: Optional[str] = None

@app.get("/orders")
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).order_by(Order.created_at.desc()).all()

@app.post("/orders")
def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order_data = data.dict()
    if order_data.get("delivery_date"):
        order_data["delivery_date"] = datetime.fromisoformat(order_data["delivery_date"])
    
    new_order = Order(**order_data, status="Orçamento")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if "status" in data: 
        old_status = order.status
        new_status = data["status"]
        order.status = new_status
        
        # --- GESTÃO DE IMPRESSORA ---
        if new_status == "Pronto" and old_status != "Pronto":
            order.finished_at = datetime.utcnow()
            # Liberar impressora e registrar horas
            if order.printer_id:
                printer = db.query(Printer).filter(Printer.id == order.printer_id).first()
                if printer: 
                    printer.status = "Disponível"
                    printer.total_hours += order.time_hours
        
        # Nota: A baixa de estoque é feita manualmente pelo frontend via /inventory/ID
        # para garantir precisão do material utilizado.

    if "paid_amount" in data:
        order.paid_amount = data["paid_amount"]
        # Atualizar status de pagamento
        if order.paid_amount >= order.suggested_price:
            order.payment_status = "Pago"
        elif order.paid_amount > 0:
            order.payment_status = "Parcial"
        else:
            order.payment_status = "Pendente"

    if "printer_id" in data:
        order.printer_id = data["printer_id"]
        # Marcar impressora como ocupada
        printer = db.query(Printer).filter(Printer.id == data["printer_id"]).first()
        if printer: printer.status = "Ocupada"
        
    db.commit()
    return order

# --- INVENTÁRIO ---

@app.get("/inventory")
def list_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Inventory).all()

@app.post("/inventory")
def create_inventory_item(data: dict, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    new_item = Inventory(**data)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.patch("/inventory/{item_id}")
def update_inventory_item(item_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    for key, val in data.items(): setattr(item, key, val)
    db.commit()
    return item

@app.delete("/inventory/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Material não encontrado.")
    db.delete(item)
    db.commit()
    return {"message": "Material removido com sucesso"}

@app.post("/inventory/{item_id}/consume")
def consume_inventory_item(item_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Material não encontrado.")
    
    weight_to_consume = data.get("weight_g", 0)
    if weight_to_consume > 0:
        item.weight_g -= weight_to_consume
        if item.weight_g < 0:
            item.weight_g = 0
        db.commit()
        db.refresh(item)
    return item

# --- GESTÃO DE CUPONS ---

class DiscountCreate(BaseModel):
    code: str
    type: str # 'percentage' ou 'fixed'
    value: float

@app.get("/discounts")
def list_discounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Discount).all()

@app.post("/discounts")
def create_discount(data: DiscountCreate, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    print(f"Criando cupom: {data}")
    # Verificar se já existe
    existing = db.query(Discount).filter(Discount.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este código de cupom já existe.")
    
    new_coupon = Discount(
        code=data.code.upper(),
        type=data.type,
        value=data.value,
        is_active=1
    )
    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return new_coupon

@app.delete("/discounts/{discount_id}")
def delete_discount(discount_id: int, db: Session = Depends(get_db), current_user: User = Depends(check_admin)):
    coupon = db.query(Discount).filter(Discount.id == discount_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupom não encontrado.")
    db.delete(coupon)
    db.commit()
    return {"message": "Cupom removido com sucesso."}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    # Desativa o reload em produção para economizar memória e CPU
    is_prod = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not is_prod)
