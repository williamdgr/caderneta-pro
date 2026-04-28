import customtkinter as ctk
from tkinter import ttk
import re
from datetime import datetime
from services.sale_service import create_sale, get_all_sales
from services.client_service import get_all_clients

class SalesView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Registrar Venda", font=("Arial",22,"bold")).pack(pady=20)

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=10)
        form.grid_columnconfigure(1, weight=1)

        self.client_dict = {}
        self.client_label_by_id = {}
        self.client_option = ctk.CTkOptionMenu(form, values=["Selecione"])
        self.client_option.set("Selecione")
        self.client_option.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.refresh_clients_options()

        self.description_entry = ctk.CTkEntry(form, placeholder_text="Descricao do que foi vendido")
        self.description_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.amount_entry = ctk.CTkEntry(form, placeholder_text="Valor da venda")
        self.amount_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(form, text="Salvar", command=self.save_sale).grid(row=0, column=3, padx=5, pady=5)

        self.validation_label = ctk.CTkLabel(self, text="", text_color="red")
        self.validation_label.pack(pady=(2, 8))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(
            self,
            columns=("ID", "Cliente", "Descricao", "Valor", "Data"),
            show="headings",
            style="Table.Treeview",
        )
        for col in ("ID", "Cliente", "Descricao", "Valor", "Data"):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center")
        self.tree.column("ID", width=70, stretch=False)
        self.tree.column("Cliente", width=220)
        self.tree.column("Descricao", width=320)
        self.tree.column("Valor", width=120, stretch=False)
        self.tree.column("Data", width=120, stretch=False)
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_sales()

    def save_sale(self):
        self.refresh_clients_options(keep_selection=True)

        client_name = self.client_option.get()
        if client_name not in self.client_dict:
            self.show_error("Erro: selecione um cliente.")
            return

        description = (self.description_entry.get() or "").strip()
        if not description:
            self.show_error("Erro: informe a descricao da venda.")
            return

        raw_amount = (self.amount_entry.get() or "").strip()
        if not raw_amount:
            self.show_error("Erro: informe o valor da venda.")
            return

        if not re.fullmatch(r"\d+(?:[\.,]\d{1,2})?", raw_amount):
            self.show_error("Erro: valor inválido. Use até 2 casas decimais.")
            return

        amount = float(raw_amount.replace(",", "."))
        self.clear_feedback()
        create_sale(self.client_dict[client_name], description, amount)
        self.description_entry.delete(0,"end")
        self.amount_entry.delete(0,"end")
        self.load_sales()
        self.show_success("Venda salva com sucesso.")

    def refresh_clients_options(self, keep_selection=False):
        current_selection = self.client_option.get() if keep_selection else "Selecione"

        clients = get_all_clients()
        self.client_dict = {}
        self.client_label_by_id = {}

        for client in clients:
            client_id = client["id"]
            display_label = f"{client['name']} (#{client_id})"
            self.client_dict[display_label] = client_id
            self.client_label_by_id[client_id] = display_label

        option_values = list(self.client_dict.keys()) if self.client_dict else ["Selecione"]

        self.client_option.configure(values=option_values)

        selected_client_id = None
        if keep_selection and current_selection in self.client_dict:
            selected_client_id = self.client_dict[current_selection]
        elif keep_selection:
            match = re.search(r"\(#(\d+)\)$", current_selection)
            if match:
                selected_client_id = int(match.group(1))

        restored_selection = "Selecione"
        if selected_client_id is not None:
            restored_selection = self.client_label_by_id.get(selected_client_id, "Selecione")

        self.client_option.set(restored_selection)

    def load_sales(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, sale in enumerate(get_all_sales()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    sale["id"],
                    sale["client_name"],
                    sale["description"],
                    self.format_currency(sale["amount"]),
                    self.format_date(sale["date"]),
                ),
                tags=(tag,)
            )

    def format_currency(self, value):
        amount = float(value or 0)
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def format_date(self, value):
        raw_value = str(value or "").strip()
        if not raw_value:
            return ""

        date_part = raw_value.split(" ")[0]
        try:
            parsed = datetime.strptime(date_part, "%Y-%m-%d")
            return parsed.strftime("%d/%m/%Y")
        except ValueError:
            return raw_value

    def show_error(self, message):
        self.validation_label.configure(text=message, text_color="red")

    def show_success(self, message):
        self.validation_label.configure(text=message, text_color="green")

    def clear_feedback(self):
        self.validation_label.configure(text="", text_color="red")
