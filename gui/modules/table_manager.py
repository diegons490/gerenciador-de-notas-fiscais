# gui/modules/table_manager.py
"""
Module for managing generic tables (Invoices, Customers, etc.) using grid.
"""

import re
from datetime import datetime

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview
from core import utils
from ..utils.popups import show_error


class SortManager:
    """Custom sorting manager for tables"""

    @staticmethod
    def sort_numeric_currency(value):
        """Converts currency values to numeric"""
        if not value or value == "-":
            return 0.0

        # Remove everything that's not a digit or comma (keeps decimal separator)
        cleaned = re.sub(r"[^\d,]", "", str(value))
        # Replace comma with dot for float
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except Exception:
            return 0.0

    @staticmethod
    def sort_date(value):
        """Converts dates to datetime object for sorting"""
        if not value or value == "-":
            return datetime.min

        try:
            return datetime.strptime(str(value), "%d/%m/%Y")
        except Exception:
            # fallback trying ISO
            try:
                return datetime.strptime(str(value), "%Y-%m-%d")
            except Exception:
                return datetime.min

    @staticmethod
    def sort_numeric(value):
        """Converts simple numeric values"""
        if not value or value == "-":
            return 0

        try:
            return int(re.sub(r"[^\d]", "", str(value)))
        except Exception:
            return 0

    @staticmethod
    def sort_string(value):
        """Case-insensitive string sorting"""
        return (str(value) or "").lower()

    @staticmethod
    def sort_phone(value):
        """Specific sorting for phones"""
        if not value:
            return ""
        return re.sub(r"[^\d]", "", str(value))

    @staticmethod
    def sort_cnpj(value):
        """Specific sorting for CNPJ"""
        if not value:
            return ""
        return re.sub(r"[^\d]", "", str(value))

    def configure_column_sorting(self, treeview, col_id, sort_function):
        """Configures custom sorting for a specific column"""

        def sort_by_column(reverse):
            # Get all items (cell value, item_id)
            items = [
                (treeview.set(child, col_id), child)
                for child in treeview.get_children("")
            ]

            # Sort using custom function (applied to cell value)
            items.sort(key=lambda x: sort_function(x[0]), reverse=reverse)

            # Reorganize items in treeview
            for index, (_, child) in enumerate(items):
                treeview.move(child, "", index)

            # Reconfigure heading to invert next time
            treeview.heading(col_id, command=lambda: sort_by_column(not reverse))

        # Configure initial heading (ascending order first time)
        treeview.heading(col_id, command=lambda: sort_by_column(False))


class BaseTableManager:
    """Base class for managing generic tables."""

    def __init__(self, database):
        self.database = database
        self.table = None
        self.selected_ids = []
        self.all_data = []
        self.filtered_data = []
        self.sort_manager = SortManager()

    def bind_selection_event(self, callback):
        """Binds table selection event."""
        if self.table and hasattr(self.table, "view"):
            self.table.view.bind("<<TreeviewSelect>>", callback)

    def get_selected_ids(self):
        """Gets IDs of selected items."""
        if not self.table or not hasattr(self.table, "view"):
            return []

        selected_iids = list(self.table.view.selection())
        selected_ids = []

        for iid in selected_iids:
            try:
                values = self.table.view.item(iid).get("values", [])
                if values:
                    selected_ids.append(int(values[0]))
            except Exception:
                continue
        return selected_ids

    def clear_selection(self):
        """Clears table selection."""
        if self.table and hasattr(self.table, "view"):
            self.table.view.selection_remove(self.table.view.selection())


class InvoicesTableManager(BaseTableManager):
    """Manages Invoices table."""

    def create_table(self, parent):
        list_frame = ttk.LabelFrame(
            parent, text="Notas Fiscais Cadastradas", bootstyle=INFO
        )
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        table_container = ttk.Frame(list_frame)
        table_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        # Table columns (text -> displayed heading)
        coldata = [
            {"text": "ID", "stretch": False, "width": 50},
            {"text": "Data", "stretch": False, "width": 100},
            {"text": "Número", "stretch": False, "width": 100},
            {"text": "Cliente", "stretch": True, "width": 150},
            {"text": "Valor", "stretch": False, "width": 120},
            {"text": "Telefone", "stretch": False, "width": 120},
            {"text": "Email", "stretch": True, "width": 150},
            {"text": "CNPJ", "stretch": False, "width": 140},
            {"text": "Endereço", "stretch": True, "width": 200},
        ]

        self.table = Tableview(
            table_container,
            coldata=coldata,
            rowdata=[],
            paginated=False,
            searchable=False,
            bootstyle=PRIMARY,
            autofit=True,
            autoalign=True,
            height=15,
        )
        self.table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            table_container, orient=VERTICAL, command=self.table.view.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.view.configure(yscrollcommand=scrollbar.set)

        # Configure custom sorting (applies through current headings)
        self.configure_custom_sorting()

        return list_frame

    def configure_custom_sorting(self):
        """Configures custom sorting for each column"""
        if not self.table or not hasattr(self.table, "view"):
            return

        treeview = self.table.view

        # Map heading text to sorting function
        sort_config = {
            "ID": self.sort_manager.sort_numeric,
            "Data": self.sort_manager.sort_date,
            "Número": self.sort_manager.sort_numeric,
            "Cliente": self.sort_manager.sort_string,
            "Valor": self.sort_manager.sort_numeric_currency,
            "Telefone": self.sort_manager.sort_phone,
            "Email": self.sort_manager.sort_string,
            "CNPJ": self.sort_manager.sort_cnpj,
            "Endereço": self.sort_manager.sort_string,
        }

        # For each treeview column, discover heading text and apply function if exists
        for col_id in treeview["columns"]:
            heading_info = treeview.heading(col_id)
            heading_text = (
                heading_info.get("text")
                if isinstance(heading_info, dict)
                else heading_info
            )
            if heading_text in sort_config:
                # pass col_id (real id) to configure_column_sorting
                self.sort_manager.configure_column_sorting(
                    treeview, col_id, sort_config[heading_text]
                )

    def update_table_data(self, invoices):
        """Updates table data."""
        try:
            rowdata = []
            for invoice in invoices:
                # Ensure we have at least 9 elements
                invoice = (
                    tuple(list(invoice) + [""] * (9 - len(invoice)))
                    if len(invoice) < 9
                    else invoice
                )

                invoice_id = invoice[0]
                date_br = invoice[1] if len(invoice) > 1 else "-"
                number = invoice[2] if len(invoice) > 2 else "-"
                customer = invoice[3] if len(invoice) > 3 else "-"
                value = utils.format_currency(invoice[4]) if len(invoice) > 4 else "-"
                phone = invoice[5] if len(invoice) > 5 else ""
                email = invoice[6] if len(invoice) > 6 else ""
                cnpj = invoice[7] if len(invoice) > 7 else ""
                address = invoice[8] if len(invoice) > 8 else ""

                rowdata.append(
                    (
                        invoice_id,
                        date_br,
                        number,
                        customer,
                        value,
                        phone or "-",
                        email or "-",
                        cnpj or "-",
                        address or "-",
                    )
                )

            coldata = [
                {"text": "ID", "stretch": False, "width": 50},
                {"text": "Data", "stretch": False, "width": 100},
                {"text": "Número", "stretch": False, "width": 100},
                {"text": "Cliente", "stretch": True, "width": 150},
                {"text": "Valor", "stretch": False, "width": 120},
                {"text": "Telefone", "stretch": False, "width": 120},
                {"text": "Email", "stretch": True, "width": 150},
                {"text": "CNPJ", "stretch": False, "width": 140},
                {"text": "Endereço", "stretch": True, "width": 200},
            ]

            if hasattr(self.table, "build_table_data"):
                # Rebuild content (recreates headings internally)
                self.table.build_table_data(coldata, rowdata)
                # after rebuilding, reapply custom sorting
                self.configure_custom_sorting()
            else:
                # Fallback for older ttkbootstrap versions
                for item in self.table.view.get_children():
                    self.table.view.delete(item)
                for row in rowdata:
                    self.table.view.insert("", "end", values=row)

        except Exception as e:
            show_error(None, f"Erro ao atualizar tabela: {e}")


class CustomersTableManager(BaseTableManager):
    """Manages Customers table."""

    def create_table(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Clientes Cadastrados", bootstyle=INFO)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        table_container = ttk.Frame(list_frame)
        table_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        coldata = [
            {"text": "ID", "stretch": False, "width": 50},
            {"text": "Nome", "stretch": True, "width": 150},
            {"text": "Telefone", "stretch": True, "width": 120},
            {"text": "Email", "stretch": True, "width": 150},
            {"text": "CNPJ", "stretch": True, "width": 120},
            {"text": "Endereço", "stretch": True, "width": 200},
        ]

        self.table = Tableview(
            table_container,
            coldata=coldata,
            rowdata=[],
            paginated=False,
            searchable=False,
            bootstyle=PRIMARY,
            autofit=True,
            autoalign=True,
            height=15,
        )
        self.table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            table_container, orient=VERTICAL, command=self.table.view.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.view.configure(yscrollcommand=scrollbar.set)

        # Configure custom sorting
        self.configure_custom_sorting()

        return list_frame

    def configure_custom_sorting(self):
        """Configures custom sorting for each column"""
        if not self.table or not hasattr(self.table, "view"):
            return

        treeview = self.table.view

        sort_config = {
            "ID": self.sort_manager.sort_numeric,
            "Nome": self.sort_manager.sort_string,
            "Telefone": self.sort_manager.sort_phone,
            "Email": self.sort_manager.sort_string,
            "CNPJ": self.sort_manager.sort_cnpj,
            "Endereço": self.sort_manager.sort_string,
        }

        for col_id in treeview["columns"]:
            heading_info = treeview.heading(col_id)
            heading_text = (
                heading_info.get("text")
                if isinstance(heading_info, dict)
                else heading_info
            )
            if heading_text in sort_config:
                self.sort_manager.configure_column_sorting(
                    treeview, col_id, sort_config[heading_text]
                )

    def update_table_data(self, customers):
        """Updates customers table data."""
        try:
            rowdata = []
            for customer in customers:
                customer = (
                    tuple(list(customer) + [""] * (6 - len(customer)))
                    if len(customer) < 6
                    else customer
                )

                customer_id = customer[0]
                name = customer[1] if len(customer) > 1 else "-"
                phone = customer[2] if len(customer) > 2 else "-"
                email = customer[3] if len(customer) > 3 else "-"
                cnpj = customer[4] if len(customer) > 4 else "-"
                address = customer[5] if len(customer) > 5 else "-"

                rowdata.append(
                    (
                        customer_id,
                        name or "-",
                        phone or "-",
                        email or "-",
                        cnpj or "-",
                        address or "-",
                    )
                )

            coldata = [
                {"text": "ID", "stretch": False, "width": 50},
                {"text": "Nome", "stretch": True, "width": 150},
                {"text": "Telefone", "stretch": True, "width": 120},
                {"text": "Email", "stretch": True, "width": 150},
                {"text": "CNPJ", "stretch": True, "width": 120},
                {"text": "Endereço", "stretch": True, "width": 200},
            ]

            if hasattr(self.table, "build_table_data"):
                self.table.build_table_data(coldata, rowdata)
                # reapply sorting after rebuild
                self.configure_custom_sorting()
            else:
                for item in self.table.view.get_children():
                    self.table.view.delete(item)
                for row in rowdata:
                    self.table.view.insert("", "end", values=row)

        except Exception as e:
            show_error(None, f"Erro ao atualizar tabela de clientes: {e}")


# Factory for creating table managers
class TableManagerFactory:
    @staticmethod
    def create_table_manager(manager_type, database):
        if manager_type == "invoices":
            return InvoicesTableManager(database)
        elif manager_type == "customers":
            return CustomersTableManager(database)
        else:
            raise ValueError(f"Tipo de manager desconhecido: {manager_type}")