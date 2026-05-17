import sqlite3
import os

db_path = os.path.join("..", "data", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'DEV' WHERE username = 'admin'")
    conn.commit()
    print("Sucesso: Admin agora é DEV.")
except Exception as e:
    print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
