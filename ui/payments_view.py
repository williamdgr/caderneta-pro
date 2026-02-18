import customtkinter as ctk
from tkinter import ttk
import re
from datetime import datetime
from services.payment_service import create_payment, get_all_payments
from services.client_service import get_all_clients

class PaymentsView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Registrar Pagamento Parcial", font=("Arial",22,"bold")).pack(pady=20)

        form = ctk.CTkFrame(self)
        form.pack(pady=10)

        self.client_dict = {}
        self.client_label_by_id = {}
        self.client_option = ctk.CTkOptionMenu(form, values=["Selecione"])
        self.client_option.set("Selecione")
        self.client_option.pack(side="left", padx=5)
        self.refresh_clients_options()

        self.amount_entry = ctk.CTkEntry(form, placeholder_text="Valor recebido")
        self.amount_entry.pack(side="left", padx=5)

        ctk.CTkButton(form, text="Registrar", command=self.save_payment).pack(side="left", padx=5)

        self.validation_label = ctk.CTkLabel(self, text="", text_color="red")
        self.validation_label.pack(pady=(2, 8))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(self, columns=("ID", "Cliente", "Valor", "Data"), show="headings", style="Table.Treeview")
        for col in ("ID", "Cliente", "Valor", "Data"):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center")
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_payments()

    def save_payment(self):
        self.refresh_clients_options(keep_selection=True)

        client_name = self.client_option.get()
        if client_name not in self.client_dict:
            self.show_error("Erro: selecione um cliente.")
            return

        raw_amount = (self.amount_entry.get() or "").strip()
        if not raw_amount:
            self.show_error("Erro: informe o valor recebido.")
            return

        if not re.fullmatch(r"\d+(?:[\.,]\d{1,2})?", raw_amount):
            self.show_error("Erro: valor inválido. Use até 2 casas decimais.")
            return

        amount = float(raw_amount.replace(",", "."))
        self.clear_feedback()
        create_payment(self.client_dict[client_name], amount)
        self.amount_entry.delete(0,"end")
        self.load_payments()
        self.show_success("Pagamento registrado com sucesso.")

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

    def load_payments(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, payment in enumerate(get_all_payments()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    payment["id"],
                    payment["client_name"],
                    self.format_currency(payment["amount"]),
                    self.format_date(payment["date"]),
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
