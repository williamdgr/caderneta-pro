from database.connection import get_connection

def get_dashboard_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM clients")
    total_clients = cursor.fetchone()["total"]

    cursor.execute("SELECT COALESCE(SUM(amount),0) as total FROM sales")
    total_sales = cursor.fetchone()["total"]

    cursor.execute("SELECT COALESCE(SUM(amount),0) as total FROM payments")
    total_paid = cursor.fetchone()["total"]

    total_open = total_sales - total_paid

    conn.close()

    return {
        "total_clients": total_clients,
        "total_sales": total_sales,
        "total_paid": total_paid,
        "total_open": total_open
    }
