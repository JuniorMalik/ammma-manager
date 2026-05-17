import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "..", "data", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Adicionar coluna client_name à tabela orders se não existir
    cursor.execute("ALTER TABLE orders ADD COLUMN client_name TEXT DEFAULT 'Consumidor Final'")
    conn.commit()
    print("Coluna client_name adicionada à tabela orders com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("A coluna client_name já existe na tabela orders.")
    else:
        print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
