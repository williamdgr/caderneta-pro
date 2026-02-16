import customtkinter as ctk
from tkinter import ttk
import re
from services.payment_service import create_payment, get_all_payments
from services.client_service import get_all_clients

class PaymentsView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Registrar Pagamento Parcial", font=("Arial",22,"bold")).pack(pady=20)

        form = ctk.CTkFrame(self)
        form.pack(pady=10)

        self.clients = get_all_clients()
        self.client_dict = {c["name"]: c["id"] for c in self.clients}

        option_values = list(self.client_dict.keys()) if self.client_dict else ["Selecione"]
        self.client_option = ctk.CTkOptionMenu(form, values=option_values)
        self.client_option.set("Selecione")
        self.client_option.pack(side="left", padx=5)

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

    def load_payments(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, payment in enumerate(get_all_payments()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(payment["id"], payment["client_name"], payment["amount"], payment["date"]),
                tags=(tag,)
            )

    def show_error(self, message):
        self.validation_label.configure(text=message, text_color="red")

    def show_success(self, message):
        self.validation_label.configure(text=message, text_color="green")

    def clear_feedback(self):
        self.validation_label.configure(text="", text_color="red")
