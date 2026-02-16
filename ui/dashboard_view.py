import customtkinter as ctk
from services.dashboard_service import get_dashboard_data

class DashboardView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        data = get_dashboard_data()

        ctk.CTkLabel(self, text="Resumo Financeiro", font=("Arial", 26, "bold")).pack(pady=(24, 6))
        ctk.CTkLabel(self, text="Visão geral do desempenho atual", font=("Arial", 14)).pack(pady=(0, 18))

        cards_container = ctk.CTkFrame(self)
        cards_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cards_container.grid_columnconfigure((0, 1), weight=1)
        cards_container.grid_rowconfigure((0, 1), weight=1)

        self.create_metric_card(cards_container, "Clientes", str(data["total_clients"]), 0, 0, value_color="#3B82F6")
        self.create_metric_card(cards_container, "Total Vendido", self.format_currency(data["total_sales"]), 0, 1, value_color="#F59E0B")
        self.create_metric_card(cards_container, "Total Recebido", self.format_currency(data["total_paid"]), 1, 0, value_color="#10B981")
        self.create_metric_card(cards_container, "Em Aberto", self.format_currency(data["total_open"]), 1, 1, highlight=True, value_color="#EF4444")

    def create_metric_card(self, parent, title, value, row, column, highlight=False, value_color="#FFFFFF"):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=0)

        title_font = ("Arial", 16, "bold")
        value_font = ("Arial", 34, "bold") if highlight else ("Arial", 30, "bold")

        ctk.CTkLabel(content, text=title, font=title_font, justify="center").pack(pady=(0, 6))
        ctk.CTkLabel(content, text=value, font=value_font, justify="center", text_color=value_color).pack()

    def format_currency(self, amount):
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
