import sqlite3
import os

db_path = os.path.join("..", "data", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Adicionar coluna se não existir
    cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    conn.commit()
    print("Coluna is_active adicionada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("A coluna is_active já existe.")
    else:
        print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
