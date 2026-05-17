import sqlite3
import os
from auth import get_password_hash

db_path = os.path.join("..", "data", "database.db")
new_password = "AM3D@MGR#1"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Atualizar senha e garantir que o cargo seja DEV
    hashed_pass = get_password_hash(new_password)
    cursor.execute("UPDATE users SET hashed_password = ?, role = 'DEV' WHERE username = 'admin'", (hashed_pass,))
    
    conn.commit()
    print("Senha do Admin (DEV) atualizada com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
