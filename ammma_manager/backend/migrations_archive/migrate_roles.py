import sqlite3
import os

db_path = os.path.join("..", "data", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Adicionar coluna role se não existir
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'colaborador'")
    # Garantir que o usuário admin tenha o cargo de admin
    cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
    conn.commit()
    print("Coluna role adicionada e configurada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("A coluna role já existe.")
    else:
        print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
