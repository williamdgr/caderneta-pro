import customtkinter as ctk
from tkinter import ttk
import re
from services.client_service import get_all_clients, create_client

class ClientsView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Clientes", font=("Arial", 22, "bold")).pack(pady=20)

        form = ctk.CTkFrame(self)
        form.pack(pady=10)

        self.name_entry = ctk.CTkEntry(form, placeholder_text="Nome")
        self.name_entry.pack(side="left", padx=5)

        self.phone_entry = ctk.CTkEntry(form, placeholder_text="Telefone")
        self.phone_entry.pack(side="left", padx=5)
        self.phone_entry.bind("<KeyRelease>", self.only_digits_phone)

        self.limit_entry = ctk.CTkEntry(form, placeholder_text="Limite Crédito")
        self.limit_entry.pack(side="left", padx=5)

        ctk.CTkButton(form, text="Salvar", command=self.save_client).pack(side="left", padx=5)

        self.validation_label = ctk.CTkLabel(self, text="", text_color="red")
        self.validation_label.pack(pady=(2, 8))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(self, columns=("ID","Nome","Telefone","Limite"), show="headings", style="Table.Treeview")
        for col in ("ID","Nome","Telefone","Limite"):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center")
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_clients()

    def load_clients(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, client in enumerate(get_all_clients()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                client["id"],
                client["name"],
                client["phone"],
                client["credit_limit"]
            ), tags=(tag,))

    def save_client(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        raw_limit = (self.limit_entry.get() or "").strip()

        if not name:
            self.show_error("Erro: informe o nome.")
            return

        if not phone:
            self.show_error("Erro: informe o telefone.")
            return

        if not phone.isdigit():
            self.show_error("Erro: telefone inválido. Use apenas números.")
            return

        if not raw_limit:
            self.show_error("Erro: informe o limite de crédito.")
            return

        if not re.fullmatch(r"\d+(?:[\.,]\d{1,2})?", raw_limit):
            self.show_error("Erro: limite de crédito inválido. Use até 2 casas decimais.")
            return

        credit_limit = float(raw_limit.replace(",", "."))

        self.clear_error()

        create_client(name, phone, credit_limit)

        self.name_entry.delete(0,"end")
        self.phone_entry.delete(0,"end")
        self.limit_entry.delete(0,"end")

        self.load_clients()
        self.show_success("Cliente salvo com sucesso.")

    def only_digits_phone(self, _event=None):
        current_value = self.phone_entry.get()
        numeric_value = re.sub(r"\D", "", current_value)
        if current_value != numeric_value:
            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, numeric_value)

    def show_error(self, message):
        self.validation_label.configure(text=message, text_color="red")

    def show_success(self, message):
        self.validation_label.configure(text=message, text_color="green")

    def clear_error(self):
        self.validation_label.configure(text="", text_color="red")
