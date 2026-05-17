import sqlite3
import os

db_path = os.path.join("..", "data", "database.db")

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Iniciando migração...")
    
    # Adicionar delivery_date em orders
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN delivery_date DATETIME")
        print("Coluna 'delivery_date' adicionada em 'orders'.")
    except sqlite3.OperationalError:
        print("Coluna 'delivery_date' já existe ou erro ao adicionar.")

    # Adicionar client_id em orders (caso não exista)
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN client_id INTEGER REFERENCES clients(id)")
        print("Coluna 'client_id' adicionada em 'orders'.")
    except sqlite3.OperationalError:
        print("Coluna 'client_id' já existe.")
        
    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
