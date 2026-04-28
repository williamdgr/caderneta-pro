from database.connection import get_connection

def create_sale(client_id, description, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sales (client_id, description, amount) VALUES (?, ?, ?)",
        (client_id, description, amount),
    )
    conn.commit()
    conn.close()

def get_all_sales():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.id, c.name AS client_name, s.description, s.amount, s.date
        FROM sales s
        INNER JOIN clients c ON c.id = s.client_id
        ORDER BY s.id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
