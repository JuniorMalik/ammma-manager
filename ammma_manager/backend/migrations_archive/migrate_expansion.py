import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "..", "data", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Adicionar coluna printer_id à tabela orders
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN printer_id INTEGER")
    except sqlite3.OperationalError:
        print("Coluna printer_id já existe.")

    # Criar tabela printers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS printers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        model TEXT,
        status TEXT DEFAULT 'Disponível',
        total_hours FLOAT DEFAULT 0.0,
        maintenance_alert_hours FLOAT DEFAULT 500.0
    )
    """)

    # Criar tabela failures
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS failures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        weight_wasted_g FLOAT,
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Criar tabela gallery
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        image_path TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    print("Migração de expansão concluída com sucesso!")
except Exception as e:
    print(f"Erro na migração: {e}")
finally:
    if conn:
        conn.close()
