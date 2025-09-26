# gui/modules/edit_invoice.py
"""
Módulo para gerenciar a edição de notas fiscais existentes.
Contém funções relacionadas ao carregamento, atualização e cancelamento de edição.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core import utils
from ..utils.popups import show_error, show_info, show_warning


class EditInvoiceManager:
    """Gerencia a funcionalidade de edição de notas fiscais existentes."""

    def __init__(self, database, theme_manager):
        self.database = database
        self.theme_manager = theme_manager

    def carregar_nota_para_edicao(
        self, parent, note_id, date_entry, variables, btn_salvar
    ):
        """Carrega os dados de uma nota para edição."""
        nota = self.database.get_nota_por_id(note_id)

        if not nota:
            show_error(parent, "Nota fiscal não encontrada!")
            return False

        try:
            data, numero, cliente, valor, telefone, email, cnpj, endereco = nota

            # Processar data
            parsed = False
            if data:
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
                    try:
                        dt = datetime.strptime(data, fmt)
                        date_entry.set_date(dt)
                        variables["data_var"].set(dt.strftime("%d/%m/%Y"))
                        parsed = True
                        break
                    except Exception:
                        continue
            if not parsed:
                variables["data_var"].set(data or "")

            # Preencher outros campos
            variables["numero_var"].set(numero or "")
            variables["cliente_var"].set(cliente or "")

            try:
                variables["valor_var"].set(
                    utils.formatar_moeda(valor, com_simbolo=False)
                )
            except Exception:
                variables["valor_var"].set(str(valor) if valor is not None else "")

            variables["telefone_var"].set(telefone or "")
            variables["email_var"].set(email or "")
            variables["cnpj_var"].set(cnpj or "")
            variables["endereco_var"].set(endereco or "")

            # Configurar modo de edição
            btn_salvar.config(text="Atualizar Nota", bootstyle=WARNING)
            show_info(
                parent,
                "Nota carregada para edição. Modifique os campos e clique em Atualizar.",
            )
            return True

        except Exception as e:
            show_error(parent, f"Erro ao carregar nota: {str(e)}")
            return False

    def atualizar_nota_existente(
        self,
        parent,
        note_id,
        data,
        numero,
        cliente,
        valor,
        telefone,
        email,
        cnpj,
        endereco,
    ):
        """Atualiza uma nota fiscal existente no banco de dados."""
        try:
            valor_decimal = utils.converter_para_decimal(valor)
            data_sql = utils.formatar_data_sql(data)

            success = self.database.update_nota(
                note_id,
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
                show_info(parent, "Nota fiscal atualizada com sucesso!")
                return True
            else:
                show_error(parent, "Erro ao atualizar nota fiscal!")
                return False

        except Exception as e:
            show_error(parent, f"Erro ao atualizar nota: {str(e)}")
            return False

    def cancelar_edicao(self, parent, date_entry, variables, btn_salvar):
        """Cancela o modo de edição e volta ao estado normal."""
        self.limpar_campos(date_entry, variables)
        btn_salvar.config(text="Salvar Nota", bootstyle=SUCCESS)
        show_info(parent, "Edição cancelada. Campos limpos.")

    def limpar_campos(self, date_entry, variables):
        """Limpa todos os campos do formulário."""
        date_entry.set_date(datetime.now())
        for var in variables.values():
            var.set("")

        # Restaura a data atual
        variables["data_var"].set(datetime.now().strftime("%d/%m/%Y"))

    def validar_edicao(self, selected_ids):
        """Valida se é possível editar (apenas uma nota selecionada)."""
        if len(selected_ids) != 1:
            show_warning(self, "Selecione exatamente uma nota para editar.")
            return False
        return True
