# gui/modules/__init__.py
"""
Módulo de views da aplicação ttkbootstrap.
"""

from .backup import ConfigBackup
from .theme import ConfigTheme
from .invoice_delete import InvoiceDelete
from .invoice_export import InvoiceExport
from .main_menu import MainMenu
from .report import Report
from .customer_registration import CustomerRegistration
from .invoice_add import InvoiceAddManager
from .invoice_edit import InvoiceEditManager
from .table_manager import (
    SortManager,
    BaseTableManager,
    InvoicesTableManager,
    CustomersTableManager,
    TableManagerFactory,
)

# ------------------------------------------------------
# Exportação explícita de classes/funções públicas
# ------------------------------------------------------
__all__ = [
    # Configurações
    "ConfigBackup",
    "ConfigTheme",
    
    # Gerenciamento de Faturas
    "InvoiceDelete",
    "InvoiceExport",
    "InvoiceAddManager",
    "InvoiceEditManager",
    
    # Relatórios
    "Report",
    
    # Clientes
    "CustomerRegistration",
    
    # Interface principal
    "MainMenu",
    
    # Tabelas
    "SortManager",
    "BaseTableManager",
    "InvoicesTableManager",
    "CustomersTableManager",
    "TableManagerFactory",
]