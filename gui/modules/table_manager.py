# gui/modules/table_manager.py
"""
Módulo para gerenciar tabelas genéricas (Notas, Clientes, etc.) usando grid.
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
    """Gerenciador de ordenação personalizada para tabelas"""

    @staticmethod
    def sort_numeric_currency(value):
        """Converte valores monetários para numéricos"""
        if not value or value == "-":
            return 0.0

        # Remove tudo que não seja dígito ou vírgula (mantém separador decimal)
        cleaned = re.sub(r"[^\d,]", "", str(value))
        # Trocar vírgula por ponto para float
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except Exception:
            return 0.0

    @staticmethod
    def sort_date(value):
        """Converte datas para objeto datetime para ordenação"""
        if not value or value == "-":
            return datetime.min

        try:
            return datetime.strptime(str(value), "%d/%m/%Y")
        except Exception:
            # fallback tentando ISO
            try:
                return datetime.strptime(str(value), "%Y-%m-%d")
            except Exception:
                return datetime.min

    @staticmethod
    def sort_numeric(value):
        """Converte valores numéricos simples"""
        if not value or value == "-":
            return 0

        try:
            return int(re.sub(r"[^\d]", "", str(value)))
        except Exception:
            return 0

    @staticmethod
    def sort_string(value):
        """Ordenação case-insensitive para strings"""
        return (str(value) or "").lower()

    @staticmethod
    def sort_telefone(value):
        """Ordenação específica para telefones"""
        if not value:
            return ""
        return re.sub(r"[^\d]", "", str(value))

    @staticmethod
    def sort_cnpj(value):
        """Ordenação específica para CNPJ"""
        if not value:
            return ""
        return re.sub(r"[^\d]", "", str(value))

    def configure_column_sorting(self, treeview, col_id, sort_function):
        """Configura a ordenação personalizada para uma coluna específica"""

        def sort_by_column(reverse):
            # Obter todos os itens (valor da célula, item_id)
            items = [
                (treeview.set(child, col_id), child)
                for child in treeview.get_children("")
            ]

            # Ordenar usando a função personalizada (aplicada ao valor da célula)
            items.sort(key=lambda x: sort_function(x[0]), reverse=reverse)

            # Reorganizar itens na treeview
            for index, (_, child) in enumerate(items):
                treeview.move(child, "", index)

            # Reconfigurar o heading para inverter na próxima vez
            treeview.heading(col_id, command=lambda: sort_by_column(not reverse))

        # Configurar heading inicial (ordenação ascendente na primeira vez)
        treeview.heading(col_id, command=lambda: sort_by_column(False))


class BaseTableManager:
    """Classe base para gerenciar tabelas genéricas."""

    def __init__(self, database):
        self.database = database
        self.table = None
        self.selected_ids = []
        self.all_data = []
        self.filtered_data = []
        self.sort_manager = SortManager()

    def bind_selection_event(self, callback):
        """Vincula evento de seleção da tabela."""
        if self.table and hasattr(self.table, "view"):
            self.table.view.bind("<<TreeviewSelect>>", callback)

    def get_selected_ids(self):
        """Obtém os IDs dos itens selecionados."""
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
        """Limpa a seleção da tabela."""
        if self.table and hasattr(self.table, "view"):
            self.table.view.selection_remove(self.table.view.selection())


class NotesTableManager(BaseTableManager):
    """Gerencia a tabela de Notas Fiscais."""

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

        # Colunas da tabela (text -> heading exibido)
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

        # Configurar ordenação personalizada (aplica pelos headings atuais)
        self.configure_custom_sorting()

        return list_frame

    def configure_custom_sorting(self):
        """Configura a ordenação personalizada para cada coluna"""
        if not self.table or not hasattr(self.table, "view"):
            return

        treeview = self.table.view

        # Mapear texto do heading para função de ordenação
        sort_config = {
            "ID": self.sort_manager.sort_numeric,
            "Data": self.sort_manager.sort_date,
            "Número": self.sort_manager.sort_numeric,
            "Cliente": self.sort_manager.sort_string,
            "Valor": self.sort_manager.sort_numeric_currency,
            "Telefone": self.sort_manager.sort_telefone,
            "Email": self.sort_manager.sort_string,
            "CNPJ": self.sort_manager.sort_cnpj,
            "Endereço": self.sort_manager.sort_string,
        }

        # Para cada coluna do treeview, descobrir o texto do heading e aplicar função se houver
        for col_id in treeview["columns"]:
            heading_info = treeview.heading(col_id)
            heading_text = (
                heading_info.get("text")
                if isinstance(heading_info, dict)
                else heading_info
            )
            if heading_text in sort_config:
                # passar col_id (id real) para configure_column_sorting
                self.sort_manager.configure_column_sorting(
                    treeview, col_id, sort_config[heading_text]
                )

    def update_table_data(self, notes):
        """Atualiza os dados da tabela."""
        try:
            rowdata = []
            for note in notes:
                # Garantir que temos pelo menos 9 elementos
                note = (
                    tuple(list(note) + [""] * (9 - len(note)))
                    if len(note) < 9
                    else note
                )

                nid = note[0]
                data_br = note[1] if len(note) > 1 else "-"
                numero = note[2] if len(note) > 2 else "-"
                cliente = note[3] if len(note) > 3 else "-"
                valor = utils.formatar_moeda(note[4]) if len(note) > 4 else "-"
                telefone = note[5] if len(note) > 5 else ""
                email = note[6] if len(note) > 6 else ""
                cnpj = note[7] if len(note) > 7 else ""
                endereco = note[8] if len(note) > 8 else ""

                rowdata.append(
                    (
                        nid,
                        data_br,
                        numero,
                        cliente,
                        valor,
                        telefone or "-",
                        email or "-",
                        cnpj or "-",
                        endereco or "-",
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
                # Reconstruir conteúdo (recria headings internamente)
                self.table.build_table_data(coldata, rowdata)
                # depois de reconstruir, reaplicar a ordenação personalizada
                self.configure_custom_sorting()
            else:
                # Fallback para versões mais antigas do ttkbootstrap
                for item in self.table.view.get_children():
                    self.table.view.delete(item)
                for row in rowdata:
                    self.table.view.insert("", "end", values=row)

        except Exception as e:
            show_error(None, f"Erro ao atualizar tabela: {e}")


class ClientsTableManager(BaseTableManager):
    """Gerencia a tabela de Clientes."""

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

        # Configurar ordenação personalizada
        self.configure_custom_sorting()

        return list_frame

    def configure_custom_sorting(self):
        """Configura a ordenação personalizada para cada coluna"""
        if not self.table or not hasattr(self.table, "view"):
            return

        treeview = self.table.view

        sort_config = {
            "ID": self.sort_manager.sort_numeric,
            "Nome": self.sort_manager.sort_string,
            "Telefone": self.sort_manager.sort_telefone,
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

    def update_table_data(self, clients):
        try:
            rowdata = []
            for client in clients:
                client = (
                    tuple(list(client) + [""] * (6 - len(client)))
                    if len(client) < 6
                    else client
                )

                cid = client[0]
                nome = client[1] if len(client) > 1 else "-"
                telefone = client[2] if len(client) > 2 else "-"
                email = client[3] if len(client) > 3 else "-"
                cnpj = client[4] if len(client) > 4 else "-"
                endereco = client[5] if len(client) > 5 else "-"

                rowdata.append(
                    (
                        cid,
                        nome or "-",
                        telefone or "-",
                        email or "-",
                        cnpj or "-",
                        endereco or "-",
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
                # reaplicar ordenação após rebuild
                self.configure_custom_sorting()
            else:
                for item in self.table.view.get_children():
                    self.table.view.delete(item)
                for row in rowdata:
                    self.table.view.insert("", "end", values=row)

        except Exception as e:
            show_error(None, f"Erro ao atualizar tabela de clientes: {e}")


# Factory para criar os table managers
class TableManagerFactory:
    @staticmethod
    def create_table_manager(manager_type, database):
        if manager_type == "notes":
            return NotesTableManager(database)
        elif manager_type == "clients":
            return ClientsTableManager(database)
        else:
            raise ValueError(f"Tipo de manager desconhecido: {manager_type}")
