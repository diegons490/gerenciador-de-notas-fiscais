# gui/modules/__init__.py
"""
Módulo de views da aplicação ttkbootstrap.
"""

from .backup import ConfigBackup
from .theme import ConfigTheme
from .delete_note import DeleteNotes
from .export_note import ExportNotes
from .main_menu import MainMenu
from .report import Report
from .cadastro_cliente import CadastroCliente
from .add_invoice import AddInvoiceManager
from .edit_invoice import EditInvoiceManager
from .table_manager import (
    SortManager,
    BaseTableManager,
    NotesTableManager,
    ClientsTableManager,
    TableManagerFactory,
)
from .search_manager import SearchManager

# ------------------------------------------------------
# Exportação explícita de classes/funções públicas
# ------------------------------------------------------
__all__ = [
    # Configurações
    "ConfigBackup",
    "ConfigTheme",
    # Notas fiscais
    "DeleteNotes",
    "ExportNotes",
    "AddInvoiceManager",
    "EditInvoiceManager",
    # Relatórios
    "Report",
    # Clientes
    "CadastroCliente",
    # Interface principal
    "MainMenu",
    # Tabelas
    "SortManager",
    "BaseTableManager",
    "NotesTableManager",
    "ClientsTableManager",
    "TableManagerFactory",
    # Pesquisa
    "SearchManager",
]
