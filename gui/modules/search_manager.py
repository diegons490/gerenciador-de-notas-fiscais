# gui/modules/search_manager.py
"""
Módulo para gerenciar a funcionalidade de pesquisa usando grid.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ..utils import create_info_tooltip
from ..utils.popups import show_info, show_error


class SearchManager:
    """Gerencia a barra de pesquisa e combobox de clientes usando grid."""

    def __init__(self, database):
        self.database = database
        self.search_var = tk.StringVar()
        self.cliente_combobox = None

    def create_search_bar(self, parent, on_search_callback):
        """Cria a barra de pesquisa usando grid."""
        search_frame = ttk.Frame(parent)
        search_frame.columnconfigure(1, weight=1)  # Campo de pesquisa expande

        ttk.Label(search_frame, text="Pesquisar:").grid(
            row=0, column=0, padx=(0, 10), sticky="w"
        )

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        search_entry.bind("<KeyRelease>", on_search_callback)

        btn_clear = ttk.Button(
            search_frame, text="Limpar", width=10, command=self.clear_search
        )
        btn_clear.grid(row=0, column=2)

        return search_frame

    def create_cliente_combobox(
        self, parent, on_cliente_selected, limpar_selecao_callback
    ):
        """Cria a combobox de seleção de clientes usando grid."""
        cliente_frame = ttk.LabelFrame(
            parent, text="Seleção Rápida de Cliente", bootstyle=SUCCESS
        )
        cliente_frame.columnconfigure(1, weight=1)

        ttk.Label(cliente_frame, text="Cliente Cadastrado:").grid(
            row=0, column=0, sticky="w", padx=(10, 5), pady=10
        )

        self.cliente_combobox = ttk.Combobox(
            cliente_frame, state="readonly", postcommand=self.carregar_clientes
        )
        self.cliente_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        self.cliente_combobox.bind("<<ComboboxSelected>>", on_cliente_selected)

        btn_limpar = ttk.Button(
            cliente_frame,
            text="Limpar Seleção",
            command=limpar_selecao_callback,
            bootstyle=SECONDARY,
            width=15,
        )
        btn_limpar.grid(row=0, column=2, padx=(5, 10), pady=10)

        self.carregar_clientes()
        return cliente_frame

    def carregar_clientes(self):
        """Carrega a lista de clientes na combobox."""
        try:
            clientes = self.database.get_all_clientes()
            nomes_clientes = [cliente[1] for cliente in clientes]
            self.cliente_combobox["values"] = nomes_clientes
        except Exception as e:
            print(f"Erro ao carregar clientes: {e}")

    def on_cliente_selecionado(self, event, variables):
        """Preenche os campos quando um cliente é selecionado."""
        nome_cliente = self.cliente_combobox.get()
        if not nome_cliente:
            return

        try:
            cliente = self.database.get_cliente_por_nome(nome_cliente)
            if cliente:
                _, nome, telefone, email, cnpj, endereco = cliente
                variables["cliente_var"].set(nome or "")
                variables["telefone_var"].set(telefone or "")
                variables["email_var"].set(email or "")
                variables["cnpj_var"].set(cnpj or "")
                variables["endereco_var"].set(endereco or "")
                show_info(None, f"Dados do cliente '{nome}' carregados com sucesso!")
        except Exception as e:
            show_error(None, f"Erro ao carregar dados do cliente: {e}")

    def limpar_selecao_cliente(self, variables):
        """Limpa a seleção do cliente."""
        self.cliente_combobox.set("")
        for field in [
            "cliente_var",
            "telefone_var",
            "email_var",
            "cnpj_var",
            "endereco_var",
        ]:
            variables[field].set("")
        show_info(None, "Seleção de cliente limpa.")

    def clear_search(self):
        """Limpa o termo de pesquisa."""
        self.search_var.set("")

    def get_search_term(self):
        """Retorna o termo de pesquisa."""
        return self.search_var.get().strip()

    def filter_notes(self, all_notes, termo):
        """Filtra as notas com base no termo de pesquisa."""
        if not termo:
            return all_notes.copy()

        try:
            return self.database.buscar_notas_por_termo(termo)
        except Exception:
            termo_l = termo.lower()
            return [
                nota
                for nota in all_notes
                if termo_l
                in (
                    str(nota[1]).lower()
                    + str(nota[2]).lower()
                    + str(nota[3]).lower()
                    + str(nota[4]).lower()
                )
            ]
