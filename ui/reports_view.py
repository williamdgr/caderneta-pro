import customtkinter as ctk
import os
from tkinter import ttk
from database.connection import get_connection
from services.client_service import get_all_clients
from services.report_pdf_service import (
    export_balances_pdf,
    export_client_statement_pdf,
    export_financial_position_pdf,
)

class ReportsView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Central de Relatórios", font=("Arial", 24, "bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Gere PDFs e acompanhe a prévia dos saldos em aberto", font=("Arial", 13)).pack(pady=(0, 12))

        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=20, pady=(0, 8))

        general_actions = ctk.CTkFrame(actions)
        general_actions.pack(fill="x", padx=10, pady=(10, 6))
        ctk.CTkLabel(general_actions, text="Relatórios Gerais", font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=(6, 8))

        general_buttons = ctk.CTkFrame(general_actions, fg_color="transparent")
        general_buttons.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(general_buttons, text="Posição Financeira (PDF)", command=self.generate_financial_position_pdf).pack(side="left", padx=(0, 8))
        ctk.CTkButton(general_buttons, text="Saldos por Cliente (PDF)", command=self.generate_balances_pdf).pack(side="left")

        self.client_dict = {}
        client_values = ["Selecione"]

        client_actions = ctk.CTkFrame(actions)
        client_actions.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(client_actions, text="Extrato Individual", font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=(6, 8))

        client_controls = ctk.CTkFrame(client_actions, fg_color="transparent")
        client_controls.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(client_controls, text="Cliente:").pack(side="left", padx=(0, 6))

        self.client_option = ctk.CTkOptionMenu(client_controls, values=client_values)
        self.client_option.set("Selecione")
        self.client_option.pack(side="left", padx=(0, 8))
        self.refresh_clients_options()

        ctk.CTkButton(client_controls, text="Gerar Extrato (PDF)", command=self.generate_client_statement_pdf).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(pady=(0, 8))

        ctk.CTkLabel(self, text="Prévia de Saldos Devedores por Cliente", font=("Arial", 16, "bold")).pack(pady=(2, 6))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(self, columns=("Cliente","Saldo"), show="headings", style="Table.Treeview")
        self.tree.heading("Cliente", text="Cliente", anchor="center")
        self.tree.heading("Saldo", text="Saldo Devedor", anchor="center")
        self.tree.column("Cliente", anchor="center")
        self.tree.column("Saldo", anchor="center")
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.id,
                   c.name,
                   COALESCE(SUM(s.amount),0) - COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.client_id = c.id),0) as saldo
            FROM clients c
            LEFT JOIN sales s ON c.id = s.client_id
            GROUP BY c.id
        """)

        rows = cursor.fetchall()
        conn.close()

        visible_idx = 0
        for row in rows:
            if row["saldo"] > 0:
                tag = "evenrow" if visible_idx % 2 == 0 else "oddrow"
                client_label = f"{row['name']} (#{row['id']})"
                self.tree.insert("", "end", values=(client_label, self.format_currency(row["saldo"])), tags=(tag,))
                visible_idx += 1

    def format_currency(self, value):
        amount = float(value or 0)
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def refresh_clients_options(self):
        clients = get_all_clients()
        self.client_dict = {f"{c['name']} (#{c['id']})": c["id"] for c in clients}

        option_values = list(self.client_dict.keys()) if self.client_dict else ["Selecione"]
        self.client_option.configure(values=option_values)
        self.client_option.set("Selecione")

    def generate_financial_position_pdf(self):
        try:
            report_path = export_financial_position_pdf()
            self.open_pdf(report_path)
            self.show_success(f"PDF gerado e aberto: {report_path}")
        except Exception as exc:
            self.show_error(f"Erro ao gerar PDF: {exc}")

    def generate_balances_pdf(self):
        try:
            report_path = export_balances_pdf()
            self.open_pdf(report_path)
            self.show_success(f"PDF gerado e aberto: {report_path}")
        except Exception as exc:
            self.show_error(f"Erro ao gerar PDF: {exc}")

    def generate_client_statement_pdf(self):
        selected_name = self.client_option.get()
        if selected_name not in self.client_dict:
            self.show_error("Selecione um cliente para gerar o extrato.")
            return

        try:
            report_path = export_client_statement_pdf(self.client_dict[selected_name], selected_name)
            self.open_pdf(report_path)
            self.show_success(f"PDF gerado e aberto: {report_path}")
        except Exception as exc:
            self.show_error(f"Erro ao gerar PDF: {exc}")

    def open_pdf(self, report_path):
        os.startfile(report_path)

    def show_error(self, message):
        self.status_label.configure(text=message, text_color="red")

    def show_success(self, message):
        self.status_label.configure(text=message, text_color="green")
