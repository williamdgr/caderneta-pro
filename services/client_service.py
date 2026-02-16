from database.connection import get_connection

def get_all_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_client(name, phone, credit_limit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, phone, credit_limit) VALUES (?, ?, ?)",
        (name, phone, credit_limit)
    )
    conn.commit()
    conn.close()
