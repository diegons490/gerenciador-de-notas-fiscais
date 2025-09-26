# gui/modules/add_invoice.py
"""
Módulo para gerenciar a adição de novas notas fiscais.
Contém funções relacionadas à validação, formatação e salvamento de novas notas.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core import utils
from ..utils.popups import show_error, show_info


class AddInvoiceManager:
    """Gerencia a funcionalidade de adição de novas notas fiscais."""

    def __init__(self, database, theme_manager):
        self.database = database
        self.theme_manager = theme_manager

    def initialize_variables(self):
        """Inicializa variáveis do formulário."""
        variables = {
            "data_var": tk.StringVar(),
            "numero_var": tk.StringVar(),
            "cliente_var": tk.StringVar(),
            "valor_var": tk.StringVar(),
            "telefone_var": tk.StringVar(),
            "email_var": tk.StringVar(),
            "cnpj_var": tk.StringVar(),
            "endereco_var": tk.StringVar(),
        }
        return variables

    def on_date_selected(self, date_entry, data_var, event=None):
        """Callback quando uma data é selecionada."""
        try:
            selected_date = date_entry.get_date()
            data_var.set(selected_date.strftime("%d/%m/%Y"))
        except Exception:
            pass

    def validar_numero_nota_wrapper(self, numero_var, event=None):
        """Valida e formata o número da nota."""
        current = numero_var.get()
        if current and not current.isdigit():
            numero_var.set(utils.limpar_numero(current))

    def formatar_valor_wrapper(self, valor_var, event=None):
        """Formata o valor durante a digitação."""
        current = valor_var.get()
        if current:
            clean = utils.formatar_valor_digitacao(current)
            if current != clean:
                valor_var.set(clean)

    def aplicar_formatacao_valor_wrapper(self, valor_var, event=None):
        """Aplica formatação final ao valor quando perde o foco."""
        current = valor_var.get()
        if current:
            valor_var.set(utils.aplicar_formatacao_valor_final(current))

    def formatar_telefone_wrapper(self, telefone_var, event=None):
        """Formata o telefone durante a digitação e reposiciona o cursor no fim."""
        current = telefone_var.get()
        if current:
            formatted = utils.formatar_telefone(current)
            if current != formatted:
                # Atualiza o valor
                telefone_var.set(formatted)
                # Reposiciona o cursor no final após a atualização do widget
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def validar_email_wrapper(self, email_var, widget, event=None):
        """Valida o email quando perde o foco."""
        email = email_var.get()
        if email and not utils.validar_email(email):
            widget.configure(bootstyle=DANGER)
        else:
            widget.configure(bootstyle=PRIMARY)

    def formatar_cnpj_wrapper(self, cnpj_var, event=None):
        """Formata o CNPJ durante a digitação e reposiciona o cursor no fim."""
        current = cnpj_var.get()
        if current:
            formatted = utils.formatar_cnpj(current)
            if current != formatted:
                cnpj_var.set(formatted)
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def validar_formulario(
        self, data, numero, cliente, valor, telefone="", email="", cnpj="", endereco=""
    ):
        """Valida todos os campos do formulário."""
        # Validação dos campos obrigatórios
        valido, mensagem = utils.validar_formulario_nota(data, numero, cliente, valor)
        if not valido:
            return False, mensagem

        # Validações opcionais
        if telefone and not utils.validar_telefone(telefone):
            return False, "Telefone inválido! Use (00) 00000-0000 ou (00) 0000-0000"

        if email and not utils.validar_email(email):
            return False, "Email inválido!"

        if cnpj and not utils.validar_cnpj(cnpj):
            return False, "CNPJ inválido! Deve ter 14 dígitos."

        return True, "Formulário válido"

    def salvar_nova_nota(
        self, parent, data, numero, cliente, valor, telefone, email, cnpj, endereco
    ):
        """Salva uma nova nota fiscal no banco de dados."""
        try:
            valor_decimal = utils.converter_para_decimal(valor)
            data_sql = utils.formatar_data_sql(data)

            success = self.database.insert_nota(
                data_sql,
                numero,
                cliente,
                valor_decimal,
                telefone,
                email,
                cnpj,
                endereco,
            )

            if success:
                show_info(parent, "Nota fiscal adicionada com sucesso!")
                return True
            else:
                show_error(parent, "Número de nota já existe!")
                return False

        except Exception as e:
            show_error(parent, f"Erro ao salvar nota: {str(e)}")
            return False

    def limpar_campos(self, date_entry, variables):
        """Limpa todos os campos do formulário."""
        date_entry.set_date(datetime.now())
        for var in variables.values():
            var.set("")

        # Restaura a data atual
        variables["data_var"].set(datetime.now().strftime("%d/%m/%Y"))
