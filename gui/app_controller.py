# gui/app_controller.py
"""
Controlador principal da aplicação usando ttkbootstrap.
Gerencia a navegação entre views e coordena a lógica da aplicação.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .modules.main_menu import MainMenu
from .modules.export_note import ExportNotes
from .modules.delete_note import DeleteNotes
from .modules.report import Report
from .modules.backup import ConfigBackup
from .modules.theme import ConfigTheme
from .modules.cadastro_cliente import CadastroCliente
from .keys import EventKeys


class AppController:
    """
    Controlador principal que gerencia a navegação entre diferentes views
    e coordena a comunicação entre modelos e views.
    """

    def __init__(self, root, theme_manager, database):
        """
        Inicializa o controlador principal.
        """
        self.root = root
        self.theme_manager = theme_manager
        self.database = database
        self.current_view = None

        # Configurar o protocolo de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Método chamado quando a aplicação está fechando."""
        # Salvar o estado da janela
        self.theme_manager.save_window_state(self.root)
        # Fechar a aplicação
        self.root.destroy()

    def _switch_view(self, view_class, *args, **kwargs):
        """
        Troca para uma nova view.
        """
        # Remover view atual
        if self.current_view:
            self.current_view.destroy()

        # Criar nova view
        self.current_view = view_class(
            self.root, self, self.theme_manager, self.database, *args, **kwargs
        )

        # Usar padding fixo (10px) ao invés de LayoutConfig
        self.current_view.pack(
            fill=BOTH,
            expand=True,
            padx=10,
            pady=10,
        )

    def show_main_menu(self):
        """Exibe a view do menu principal."""
        self._switch_view(MainMenu)

    def show_cadastro_cliente(self):
        """Exibe a view de cadastro de clientes."""
        self._switch_view(CadastroCliente)

    def show_report(self):
        """Exibe a view de relatórios."""
        self._switch_view(Report)

    def show_backup(self):
        """Exibe a view de backup."""
        self._switch_view(ConfigBackup)

    def show_theme(self):
        """Exibe a view de configuração de temas."""
        self._switch_view(ConfigTheme)

    def handle_event(self, event, data=None):
        """
        Processa eventos gerados pelas views.
        """
        if event == EventKeys.BACK:
            self.show_main_menu()
        elif event == EventKeys.EXIT:
            # SALVAR ESTADO ANTES DE SAIR
            self.theme_manager.save_window_state(self.root)
            self.root.quit()
        elif event == EventKeys.CADASTRO_CLIENTES:
            self.show_cadastro_cliente()
        elif event == EventKeys.REPORT:
            self.show_report()
        elif event == EventKeys.BACKUPS:
            # O backup agora é tratado como diálogo modal no main_menu
            pass
        elif event == EventKeys.THEME:
            self.show_theme()

    def refresh_current_view(self):
        """Solicita à view atual que atualize seus dados."""
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()
