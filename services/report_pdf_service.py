from datetime import datetime
from pathlib import Path
import re

from database.connection import get_connection, get_db_path
from services.dashboard_service import get_dashboard_data

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _reports_dir():
    db_path = get_db_path()
    app_base_dir = db_path.parent.parent
    reports_path = app_base_dir / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _format_currency(amount):
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _sanitize_filename(text):
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "cliente"


def _format_cpf(value):
    digits = re.sub(r"\D", "", str(value or ""))[:11]
    if len(digits) != 11:
        return value or "-"
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"


def _base_table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def export_financial_position_pdf():
    data = get_dashboard_data()

    report_path = _reports_dir() / f"posicao_financeira_{_timestamp()}.pdf"
    doc = SimpleDocTemplate(str(report_path), pagesize=A4)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Posição Financeira", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 16),
    ]

    table_data = [
        ["Indicador", "Valor"],
        ["Clientes", str(data["total_clients"])],
        ["Total Vendido", _format_currency(data["total_sales"])],
        ["Total Recebido", _format_currency(data["total_paid"])],
        ["Em Aberto", _format_currency(data["total_open"])],
    ]

    table = Table(table_data, colWidths=[280, 200])
    table.setStyle(_base_table_style())
    elements.append(table)

    doc.build(elements)
    return str(report_path)


def _get_balances_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.id AS client_id,
            c.name AS client_name,
            COALESCE((SELECT SUM(s.amount) FROM sales s WHERE s.client_id = c.id), 0) AS total_sold,
            COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.client_id = c.id), 0) AS total_paid,
            COALESCE((SELECT SUM(s.amount) FROM sales s WHERE s.client_id = c.id), 0)
            - COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.client_id = c.id), 0) AS total_open
        FROM clients c
        ORDER BY total_open DESC, c.name ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def export_balances_pdf():
    rows = _get_balances_data()

    report_path = _reports_dir() / f"saldos_clientes_{_timestamp()}.pdf"
    doc = SimpleDocTemplate(str(report_path), pagesize=A4)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Saldos por Cliente", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 16),
    ]

    table_data = [["Cliente", "Vendido", "Recebido", "Em Aberto"]]
    for row in rows:
        client_label = f"{row['client_name']} (#{row['client_id']})"
        table_data.append(
            [
                client_label,
                _format_currency(row["total_sold"]),
                _format_currency(row["total_paid"]),
                _format_currency(row["total_open"]),
            ]
        )

    table = Table(table_data, colWidths=[190, 110, 110, 110])
    table.setStyle(_base_table_style())
    elements.append(table)

    doc.build(elements)
    return str(report_path)


def _get_client_statement_data(client_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, amount, date, 'Venda' AS entry_type
        FROM sales
        WHERE client_id = ?
        UNION ALL
        SELECT id, amount, date, 'Pagamento' AS entry_type
        FROM payments
        WHERE client_id = ?
        ORDER BY date ASC, id ASC
        """,
        (client_id, client_id),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def _get_client_basic_data(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, cpf FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def export_client_statement_pdf(client_id, client_name):
    client_data = _get_client_basic_data(client_id)
    display_name = client_data["name"] if client_data and client_data["name"] else client_name
    cpf_display = _format_cpf(client_data["cpf"] if client_data else "")

    rows = _get_client_statement_data(client_id)

    report_path = _reports_dir() / f"extrato_{_sanitize_filename(display_name)}_{_timestamp()}.pdf"
    doc = SimpleDocTemplate(str(report_path), pagesize=A4)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Extrato do Cliente", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Cliente: {display_name}", styles["Normal"]),
        Paragraph(f"CPF: {cpf_display}", styles["Normal"]),
        Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 16),
    ]

    table_data = [["Data", "Tipo", "Valor", "Saldo Acumulado"]]
    running_balance = 0.0

    for row in rows:
        amount = float(row["amount"])
        if row["entry_type"] == "Venda":
            running_balance += amount
        else:
            running_balance -= amount

        date_display = str(row["date"]).split(" ")[0]
        table_data.append(
            [
                date_display,
                row["entry_type"],
                _format_currency(amount),
                _format_currency(running_balance),
            ]
        )

    if len(table_data) == 1:
        table_data.append(["-", "Sem movimentações", "-", _format_currency(0)])

    table = Table(table_data, colWidths=[110, 130, 110, 170])
    table.setStyle(_base_table_style())
    elements.append(table)

    doc.build(elements)
    return str(report_path)
