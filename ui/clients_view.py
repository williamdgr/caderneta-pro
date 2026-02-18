import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox
import re
from services.client_service import get_all_clients, create_client, update_client, delete_client

class ClientsView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Clientes", font=("Arial", 22, "bold")).pack(pady=20)

        self.selected_client_id = None

        form = ctk.CTkFrame(self)
        form.pack(pady=10)

        fields_row = ctk.CTkFrame(form, fg_color="transparent")
        fields_row.pack(padx=5, pady=(0, 4))

        label_row = ctk.CTkFrame(form, fg_color="transparent")
        label_row.pack(padx=5, pady=(0, 4))

        buttons_row = ctk.CTkFrame(form, fg_color="transparent")
        buttons_row.pack(padx=5)

        self.editing_label = ctk.CTkLabel(label_row, text=" ", text_color="#2563eb")
        self.editing_label.pack()

        self.name_entry = ctk.CTkEntry(fields_row, placeholder_text="Nome")
        self.name_entry.pack(side="left", padx=5)

        self.phone_entry = ctk.CTkEntry(fields_row, placeholder_text="Telefone")
        self.phone_entry.pack(side="left", padx=5)
        self.phone_entry.bind("<KeyRelease>", self.only_digits_phone)

        self.limit_entry = ctk.CTkEntry(fields_row, placeholder_text="Limite Crédito")
        self.limit_entry.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(buttons_row, text="Salvar", command=self.save_client)
        self.save_button.pack(side="left", padx=5)

        self.update_button = ctk.CTkButton(buttons_row, text="Editar", command=self.edit_client, state="disabled")
        self.update_button.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(buttons_row, text="Remover", command=self.remove_client, state="disabled")
        self.delete_button.pack(side="left", padx=5)

        self.cancel_button = ctk.CTkButton(buttons_row, text="Cancelar", command=self.reset_form, state="disabled")
        self.cancel_button.pack(side="left", padx=5)

        self.validation_label = ctk.CTkLabel(self, text="", text_color="red")
        self.validation_label.pack(pady=(2, 8))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(self, columns=("ID","Nome","Telefone","Limite"), show="headings", style="Table.Treeview")
        for col in ("ID","Nome","Telefone","Limite"):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_client)
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_clients()

    def load_clients(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, client in enumerate(get_all_clients()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            display_name = f"{client['name']}"
            display_limit = self.format_currency(client["credit_limit"])
            self.tree.insert("", "end", values=(
                client["id"],
                display_name,
                client["phone"],
                display_limit
            ), tags=(tag,))

    def format_currency(self, value):
        amount = float(value or 0)
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def parse_currency(self, value):
        if value is None:
            return ""
        cleaned = str(value).replace("R$", "").strip()
        cleaned = cleaned.replace(".", "").replace(",", ".")
        return cleaned

    def validate_form(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        raw_limit = (self.limit_entry.get() or "").strip()

        if not name:
            self.show_error("Erro: informe o nome.")
            return None

        if not phone:
            self.show_error("Erro: informe o telefone.")
            return None

        if not phone.isdigit():
            self.show_error("Erro: telefone inválido. Use apenas números.")
            return None

        if not raw_limit:
            self.show_error("Erro: informe o limite de crédito.")
            return None

        if not re.fullmatch(r"\d+(?:[\.,]\d{1,2})?", raw_limit):
            self.show_error("Erro: limite de crédito inválido. Use até 2 casas decimais.")
            return None

        credit_limit = float(raw_limit.replace(",", "."))
        return name, phone, credit_limit

    def save_client(self):
        validated_data = self.validate_form()
        if not validated_data:
            return

        name, phone, credit_limit = validated_data

        self.clear_error()

        create_client(name, phone, credit_limit)

        self.reset_form()
        self.load_clients()
        self.show_success("Cliente salvo com sucesso.")

    def edit_client(self):
        if not self.selected_client_id:
            self.show_error("Erro: selecione um cliente para editar.")
            return

        validated_data = self.validate_form()
        if not validated_data:
            return

        name, phone, credit_limit = validated_data

        self.clear_error()
        update_client(self.selected_client_id, name, phone, credit_limit)
        self.reset_form()
        self.load_clients()
        self.show_success("Cliente atualizado com sucesso.")

    def remove_client(self):
        if not self.selected_client_id:
            self.show_error("Erro: selecione um cliente para remover.")
            return

        confirmed = messagebox.askyesno("Confirmar remoção", "Deseja remover o cliente selecionado?")
        if not confirmed:
            return

        was_deleted = delete_client(self.selected_client_id)
        if not was_deleted:
            self.show_error("Erro: não é possível remover cliente com registros em pagamentos ou vendas.")
            return

        self.reset_form()
        self.load_clients()
        self.show_success("Cliente removido com sucesso.")

    def on_select_client(self, _event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        values = self.tree.item(selected_items[0], "values")
        if not values:
            return

        self.selected_client_id = int(values[0])

        selected_name = values[1]
        match = re.match(r"^(.*)\s\(#\d+\)$", selected_name)
        if match:
            selected_name = match.group(1)

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, selected_name)

        self.phone_entry.delete(0, "end")
        self.phone_entry.insert(0, values[2])

        self.limit_entry.delete(0, "end")
        self.limit_entry.insert(0, self.parse_currency(values[3]))

        self.update_button.configure(state="normal")
        self.delete_button.configure(state="normal")
        self.cancel_button.configure(state="normal")
        self.save_button.configure(state="disabled")
        self.editing_label.configure(text=f"Editando cliente ID: {self.selected_client_id}")
        self.clear_error()

    def reset_form(self):
        self.selected_client_id = None

        self.name_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.limit_entry.delete(0, "end")

        selected_items = self.tree.selection()
        if selected_items:
            self.tree.selection_remove(selected_items)

        self.update_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        self.save_button.configure(state="normal")
        self.editing_label.configure(text=" ")

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
