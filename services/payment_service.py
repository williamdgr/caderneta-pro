from database.connection import get_connection

def create_payment(client_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payments (client_id, amount) VALUES (?, ?)", (client_id, amount))
    conn.commit()
    conn.close()

def get_all_payments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, c.name AS client_name, p.amount, p.date
        FROM payments p
        INNER JOIN clients c ON c.id = p.client_id
        ORDER BY p.id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
