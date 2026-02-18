import customtkinter as ctk
from app_paths import get_asset_path
from app_info import APP_NAME, APP_VERSION
from ui.dashboard_view import DashboardView
from ui.clients_view import ClientsView
from ui.sales_view import SalesView
from ui.payments_view import PaymentsView
from ui.reports_view import ReportsView
from ui.backup_view import BackupView

class MainWindow(ctk.CTk):

    def __init__(self, license_active=False):
        super().__init__()
        self.license_active = license_active

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1000x600")
        self.set_app_icon()
        self.maximize_window()

        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial",18,"bold")).pack(pady=20)

        if self.license_active:
            ctk.CTkLabel(
                self.sidebar,
                text="Licença ativada",
                font=("Arial", 12, "bold"),
                text_color="#22c55e",
            ).pack(pady=(0, 12))

        nav_buttons = [
            ("Resumo", self.show_dashboard),
            ("Clientes", self.show_clients),
            ("Vendas", self.show_sales),
            ("Pagamentos", self.show_payments),
            ("Relatórios", self.show_reports),
        ]

        for label, action in nav_buttons:
            ctk.CTkButton(self.sidebar, text=label, command=action).pack(pady=5, padx=10, fill="x")

        self.backup_label = ctk.CTkLabel(
            self.sidebar,
            text="Gerenciar Backup",
            font=("Arial", 13, "underline"),
            text_color="#3B82F6",
            cursor="hand2",
        )
        self.backup_label.pack(pady=(14, 0))
        self.backup_label.bind("<Button-1>", lambda _event: self.show_backup())

        self.main_area = ctk.CTkFrame(self)
        self.main_area.pack(side="right", fill="both", expand=True)

        self.show_dashboard()

    def clear(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear()
        DashboardView(self.main_area)

    def show_clients(self):
        self.clear()
        ClientsView(self.main_area)

    def show_sales(self):
        self.clear()
        SalesView(self.main_area)

    def show_payments(self):
        self.clear()
        PaymentsView(self.main_area)

    def show_reports(self):
        self.clear()
        ReportsView(self.main_area)

    def show_backup(self):
        self.clear()
        BackupView(self.main_area)

    def set_app_icon(self):
        icon_path = get_asset_path("icone.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

    def maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            pass
