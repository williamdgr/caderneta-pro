from database.connection import get_connection

def get_all_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            c.*,
            COALESCE((SELECT SUM(s.amount) FROM sales s WHERE s.client_id = c.id), 0)
            - COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.client_id = c.id), 0) AS total_open,
            COALESCE(c.credit_limit, 0) - (
                COALESCE((SELECT SUM(s.amount) FROM sales s WHERE s.client_id = c.id), 0)
                - COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.client_id = c.id), 0)
            ) AS available_balance
        FROM clients c
        ORDER BY c.name ASC, c.id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_client(name, cpf, phone, credit_limit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, cpf, phone, credit_limit) VALUES (?, ?, ?, ?)",
        (name, cpf, phone, credit_limit)
    )
    conn.commit()
    conn.close()

def update_client(client_id, name, cpf, phone, credit_limit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET name = ?, cpf = ?, phone = ?, credit_limit = ? WHERE id = ?",
        (name, cpf, phone, credit_limit, client_id)
    )
    conn.commit()
    conn.close()

def client_has_related_records(client_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(1) AS total FROM payments WHERE client_id = ?", (client_id,))
    payments_count = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(1) AS total FROM sales WHERE client_id = ?", (client_id,))
    sales_count = cursor.fetchone()["total"]

    conn.close()
    return (payments_count + sales_count) > 0

def delete_client(client_id):
    if client_has_related_records(client_id):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return True
