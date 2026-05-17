import sqlite3
import os

db_path = os.path.join("..", "data", "database.db")

def fix():
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar colunas existentes em orders
    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Colunas atuais: {columns}")

    missing_columns = [
        ("paid_amount", "FLOAT DEFAULT 0.0"),
        ("payment_status", "VARCHAR DEFAULT 'Pendente'"),
        ("original_price", "FLOAT"),
        ("discount_amount", "FLOAT DEFAULT 0.0"),
        ("printer_id", "INTEGER"),
        ("delivery_date", "DATETIME"),
        ("finished_at", "DATETIME")
    ]

    for col_name, col_type in missing_columns:
        if col_name not in columns:
            print(f"Adicionando coluna {col_name}...")
            try:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Erro ao adicionar {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Correção concluída.")

if __name__ == "__main__":
    fix()
