"""
Migração: Corrigir initial_amount nulo no inventário.
Atualiza todos os itens onde initial_amount é NULL,
definindo-o igual ao weight_g atual.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Buscar quantos registros estão com initial_amount nulo
cursor.execute("SELECT COUNT(*) FROM inventory WHERE initial_amount IS NULL OR initial_amount = 0")
count = cursor.fetchone()[0]
print(f"Itens com initial_amount inválido: {count}")

if count > 0:
    # Definir initial_amount = weight_g para todos os itens afetados
    cursor.execute("""
        UPDATE inventory
        SET initial_amount = weight_g
        WHERE initial_amount IS NULL OR initial_amount = 0
    """)
    conn.commit()
    print(f"Corrigidos {cursor.rowcount} item(ns) com sucesso.")
else:
    print("Nenhum item precisava de correção.")

# Mostrar estado final do inventário
cursor.execute("SELECT id, material_name, color, weight_g, initial_amount, price_paid FROM inventory")
rows = cursor.fetchall()
print("\n--- Estado atual do inventário ---")
for row in rows:
    id_, name, color, weight, initial, price = row
    unit_price = (price / initial) if (initial and price) else 0
    print(f"  ID {id_} | {name} {color} | Estoque: {weight}g | Inicial: {initial}g | Pago: R${price} | V.Unit: R${unit_price:.4f}/g")

conn.close()
print("\nMigração concluída!")
