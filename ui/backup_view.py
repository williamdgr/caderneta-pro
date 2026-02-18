import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
from pathlib import Path
from database.connection import get_db_path
from services.backup_service import create_startup_backup, get_latest_backups, restore_backup


class BackupView(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Gerenciamento de Backup", font=("Arial", 24, "bold")).pack(pady=(30, 10))

        db_path = get_db_path()
        self.backup_dir = db_path.parent / "backup"

        ctk.CTkLabel(
            self,
            text=(
                "Como fazer backup:\n"
                "1. Clique em 'Fazer backup agora'.\n"
                "2. O sistema cria uma cópia do banco com data e hora no nome.\n"
                "3. O arquivo é salvo na pasta de backup e os 7 mais recentes são mantidos.\n\n"
                f"Banco atual: {db_path}\n"
                f"Pasta de backup: {self.backup_dir}"
            ),
            font=("Arial", 14),
            justify="left",
        ).pack(pady=(0, 12), padx=20)

        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(pady=(0, 10))

        ctk.CTkButton(actions_row, text="Fazer backup agora", command=self.create_backup_now).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions_row, text="Abrir pasta de backup", command=self.open_backup_folder).pack(side="left")
        ctk.CTkButton(actions_row, text="Restaurar backup selecionado", command=self.restore_selected_backup).pack(side="left", padx=(8, 0))

        self.status_label = ctk.CTkLabel(self, text="", text_color="green", font=("Arial", 13))
        self.status_label.pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Últimos backups", font=("Arial", 16, "bold")).pack(pady=(8, 6))

        style = ttk.Style()
        style.configure("Table.Treeview", rowheight=28, borderwidth=1, relief="solid")
        style.configure("Table.Treeview.Heading", relief="solid")

        self.tree = ttk.Treeview(self, columns=("Arquivo", "Data/Hora", "Tamanho"), show="headings", style="Table.Treeview")
        for col in ("Arquivo", "Data/Hora", "Tamanho"):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center")
        self.tree.bind("<Double-1>", self.open_selected_backup)
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F3F4F6")
        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.load_backups()

    def create_backup_now(self):
        try:
            backup_path = create_startup_backup(max_files=7)
            if backup_path is None:
                self.status_label.configure(text="Nenhum banco encontrado para backup.", text_color="red")
                return

            self.status_label.configure(text=f"Backup criado com sucesso: {backup_path.name}", text_color="green")
            self.load_backups()
        except Exception as exc:
            self.status_label.configure(text=f"Erro ao criar backup: {exc}", text_color="red")

    def load_backups(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        backups = get_latest_backups(limit=7)
        if not backups:
            self.tree.insert("", "end", values=("Nenhum backup encontrado", "-", "-"), tags=("evenrow",))
            return

        for idx, backup in enumerate(backups):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    backup["name"],
                    backup["datetime"].strftime("%d/%m/%Y %H:%M:%S"),
                    self._format_size(backup["size_bytes"]),
                ),
                tags=(tag,),
            )

    def open_backup_folder(self):
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(self.backup_dir))
            self.status_label.configure(text="Pasta de backup aberta com sucesso.", text_color="green")
        except Exception as exc:
            self.status_label.configure(text=f"Erro ao abrir pasta de backup: {exc}", text_color="red")

    def open_selected_backup(self, _event=None):
        backup_file = self.get_selected_backup_file()
        if backup_file is None:
            return

        try:
            os.startfile(str(backup_file))
            self.status_label.configure(text=f"Backup aberto: {backup_file.name}", text_color="green")
        except Exception as exc:
            self.status_label.configure(text=f"Erro ao abrir backup: {exc}", text_color="red")

    def restore_selected_backup(self):
        backup_file = self.get_selected_backup_file()
        if backup_file is None:
            return

        confirmed = messagebox.askyesno(
            "Confirmar restauração",
            "Deseja restaurar o backup selecionado?\nEsta ação sobrescreve o banco de dados atual.",
        )
        if not confirmed:
            return

        try:
            restore_backup(backup_file)
            self.status_label.configure(
                text=f"Backup restaurado com sucesso: {backup_file.name}. O sistema será fechado.",
                text_color="green",
            )
            messagebox.showinfo(
                "Restauração concluída",
                "Backup restaurado com sucesso. O sistema será reiniciado para aplicar as alterações.",
            )
            self.restart_application()
        except Exception as exc:
            self.status_label.configure(text=f"Erro ao restaurar backup: {exc}", text_color="red")

    def restart_application(self):
        root = self.winfo_toplevel()

        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable], close_fds=True)
        else:
            main_path = Path(__file__).resolve().parents[1] / "main.py"
            subprocess.Popen([sys.executable, str(main_path)], cwd=str(main_path.parent), close_fds=True)

        root.after(100, root.destroy)

    def get_selected_backup_file(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.status_label.configure(text="Selecione um backup.", text_color="red")
            return None

        values = self.tree.item(selected_items[0], "values")
        if not values or values[0] == "Nenhum backup encontrado":
            self.status_label.configure(text="Nenhum arquivo de backup disponível.", text_color="red")
            return None

        backup_file = self.backup_dir / values[0]
        if not backup_file.exists():
            self.status_label.configure(text="Arquivo de backup não encontrado.", text_color="red")
            return None

        return backup_file

    def _format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.2f} MB"
