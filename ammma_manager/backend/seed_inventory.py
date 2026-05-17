"""
Seed: Adiciona todos os insumos essenciais de impressão 3D ao inventário.
Categorias: Filamento, Embalagem, Insumos
"""
import requests

BASE_URL = "http://localhost:8000"
creds = {"username": "admin", "password": "AM3D@MGR#1"}

# Login
print("Fazendo login...")
resp = requests.post(f"{BASE_URL}/login", json=creds)
if resp.status_code != 200:
    print(f"Erro no login: {resp.status_code} - {resp.text}")
    exit()

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Login OK!\n")

# Buscar inventário existente para não duplicar
resp = requests.get(f"{BASE_URL}/inventory", headers=headers)
existing = resp.json()
existing_names = set(f"{i['material_name']}|{i['color']}" for i in existing)

items = [
    # ───── FILAMENTOS ─────
    {
        "category": "Filamento", "unit": "g",
        "material_name": "PLA",       "color": "Preto",    "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 120.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "PLA",       "color": "Cinza",    "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 120.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "PETG",      "color": "Transparente", "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 140.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "PETG",      "color": "Preto",    "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 140.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "ABS",       "color": "Branco",   "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 110.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "TPU",       "color": "Natural",  "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 180.0
    },
    {
        "category": "Filamento", "unit": "g",
        "material_name": "ASA",       "color": "Cinza",    "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 160.0
    },

    # ───── EMBALAGENS ─────
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Caixa de Papelão P", "color": "-", "brand": "-",
        "weight_g": 50.0, "initial_amount": 50.0, "price_paid": 75.0,
        "min_weight_g": 5.0
    },
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Caixa de Papelão M", "color": "-", "brand": "-",
        "weight_g": 30.0, "initial_amount": 30.0, "price_paid": 60.0,
        "min_weight_g": 5.0
    },
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Saco Plástico Zip",  "color": "-", "brand": "-",
        "weight_g": 100.0, "initial_amount": 100.0, "price_paid": 20.0,
        "min_weight_g": 10.0
    },
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Papel Kraft",        "color": "-", "brand": "-",
        "weight_g": 50.0, "initial_amount": 50.0, "price_paid": 25.0,
        "min_weight_g": 5.0
    },
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Fita Adesiva",       "color": "-", "brand": "-",
        "weight_g": 10.0, "initial_amount": 10.0, "price_paid": 30.0,
        "min_weight_g": 2.0
    },
    {
        "category": "Embalagem", "unit": "un",
        "material_name": "Plástico Bolha",     "color": "-", "brand": "-",
        "weight_g": 20.0, "initial_amount": 20.0, "price_paid": 30.0,
        "min_weight_g": 3.0
    },

    # ───── INSUMOS ─────
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Cola em Bastão",     "color": "-", "brand": "-",
        "weight_g": 10.0, "initial_amount": 10.0, "price_paid": 30.0,
        "min_weight_g": 2.0
    },
    {
        "category": "Insumos", "unit": "ml",
        "material_name": "Álcool Isopropílico", "color": "-", "brand": "-",
        "weight_g": 1000.0, "initial_amount": 1000.0, "price_paid": 25.0,
        "min_weight_g": 100.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Fita Crepe Azul",    "color": "Azul", "brand": "-",
        "weight_g": 5.0, "initial_amount": 5.0, "price_paid": 35.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "ml",
        "material_name": "Lubrificante Sintético", "color": "-", "brand": "-",
        "weight_g": 100.0, "initial_amount": 100.0, "price_paid": 45.0,
        "min_weight_g": 20.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Espátula Metálica",  "color": "-", "brand": "-",
        "weight_g": 3.0, "initial_amount": 3.0, "price_paid": 30.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Agulha Limpeza Nozzle", "color": "-", "brand": "-",
        "weight_g": 10.0, "initial_amount": 10.0, "price_paid": 15.0,
        "min_weight_g": 2.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Nozzle 0.4mm",      "color": "Latão", "brand": "-",
        "weight_g": 5.0, "initial_amount": 5.0, "price_paid": 50.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Nozzle 0.6mm",      "color": "Aço", "brand": "-",
        "weight_g": 3.0, "initial_amount": 3.0, "price_paid": 60.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Lixa 220",           "color": "-", "brand": "-",
        "weight_g": 20.0, "initial_amount": 20.0, "price_paid": 15.0,
        "min_weight_g": 3.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Lixa 400",           "color": "-", "brand": "-",
        "weight_g": 20.0, "initial_amount": 20.0, "price_paid": 15.0,
        "min_weight_g": 3.0
    },
    {
        "category": "Insumos", "unit": "ml",
        "material_name": "Acetona",            "color": "-", "brand": "-",
        "weight_g": 500.0, "initial_amount": 500.0, "price_paid": 20.0,
        "min_weight_g": 50.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Luvas Nitrílica",    "color": "Azul", "brand": "-",
        "weight_g": 50.0, "initial_amount": 50.0, "price_paid": 25.0,
        "min_weight_g": 10.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Primer Spray",       "color": "Cinza", "brand": "-",
        "weight_g": 5.0, "initial_amount": 5.0, "price_paid": 40.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Pinça de Precisão",  "color": "-", "brand": "-",
        "weight_g": 3.0, "initial_amount": 3.0, "price_paid": 20.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Alicate de Bico",    "color": "-", "brand": "-",
        "weight_g": 2.0, "initial_amount": 2.0, "price_paid": 35.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Jogo Chave Allen",   "color": "-", "brand": "-",
        "weight_g": 2.0, "initial_amount": 2.0, "price_paid": 25.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Correia GT2 (m)",    "color": "-", "brand": "-",
        "weight_g": 5.0, "initial_amount": 5.0, "price_paid": 30.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Termistor NTC 100k", "color": "-", "brand": "-",
        "weight_g": 3.0, "initial_amount": 3.0, "price_paid": 25.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Resistência Bloco Quente", "color": "-", "brand": "-",
        "weight_g": 3.0, "initial_amount": 3.0, "price_paid": 20.0,
        "min_weight_g": 1.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Silicone em Bastão", "color": "-", "brand": "-",
        "weight_g": 10.0, "initial_amount": 10.0, "price_paid": 20.0,
        "min_weight_g": 2.0
    },
    {
        "category": "Insumos", "unit": "un",
        "material_name": "Máscara PFF2",       "color": "Branca", "brand": "-",
        "weight_g": 20.0, "initial_amount": 20.0, "price_paid": 30.0,
        "min_weight_g": 5.0
    },
]

added = 0
skipped = 0

for item in items:
    key = f"{item['material_name']}|{item['color']}"
    if key in existing_names:
        print(f"  [IGNORADO] {item['material_name']} {item['color']} já existe.")
        skipped += 1
        continue

    resp = requests.post(f"{BASE_URL}/inventory", json=item, headers=headers)
    if resp.status_code == 200:
        print(f"  [OK] {item['category']:10} | {item['material_name']} {item['color']}")
        added += 1
    else:
        print(f"  [ERRO] {item['material_name']}: {resp.status_code} - {resp.text}")

print(f"\n✅ Concluído! {added} item(ns) adicionado(s), {skipped} ignorado(s) (já existia).")
