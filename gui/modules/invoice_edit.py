# gui/modules/invoice_edit.py
"""
Module for managing the editing of existing invoices.
Contains functions related to loading, updating and canceling editing.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core import utils
from ..utils.popups import show_error, show_info, show_warning


class InvoiceEditManager:
    """Manages the functionality of editing existing invoices."""

    def __init__(self, database, theme_manager):
        self.database = database
        self.theme_manager = theme_manager

    def load_invoice_for_editing(self, parent, invoice_id, date_entry, variables, save_button):
        """Loads invoice data for editing."""
        invoice = self.database.get_invoice_by_id(invoice_id)

        if not invoice:
            show_error(parent, "Nota fiscal não encontrada!")
            return False

        try:
            date, number, customer, value, phone, email, cnpj, address = invoice

            parsed = False
            if date:
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
                    try:
                        dt = datetime.strptime(date, fmt)
                        date_entry.set_date(dt)
                        variables["date_var"].set(dt.strftime("%d/%m/%Y"))
                        parsed = True
                        break
                    except Exception:
                        continue
            if not parsed:
                variables["date_var"].set(date or "")

            variables["number_var"].set(number or "")
            variables["customer_var"].set(customer or "")

            try:
                variables["value_var"].set(
                    utils.format_currency(value, with_symbol=False)
                )
            except Exception:
                variables["value_var"].set(str(value) if value is not None else "")

            variables["phone_var"].set(phone or "")
            variables["email_var"].set(email or "")
            variables["cnpj_var"].set(cnpj or "")
            variables["address_var"].set(address or "")

            save_button.config(text="Atualizar Nota", bootstyle=WARNING)
            show_info(
                parent,
                "Nota carregada para edição. Modifique os campos e clique em Atualizar.",
            )
            return True

        except Exception as e:
            show_error(parent, f"Erro ao carregar nota: {str(e)}")
            return False

    def update_existing_invoice(self, parent, invoice_id, date, number, customer, 
                               value, phone, email, cnpj, address):
        """Updates an existing invoice in the database."""
        try:
            value_decimal = utils.convert_to_decimal(value)
            date_sql = utils.format_sql_date(date)

            success = self.database.update_invoice(
                invoice_id, date_sql, number, customer, value_decimal, 
                phone, email, cnpj, address
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

    def cancel_editing(self, parent, date_entry, variables, save_button):
        """Cancels edit mode and returns to normal state."""
        self.clear_fields(date_entry, variables)
        save_button.config(text="Salvar Nota", bootstyle=SUCCESS)
        show_info(parent, "Edição cancelada. Campos limpos.")

    def clear_fields(self, date_entry, variables):
        """Clears all form fields."""
        date_entry.set_date(datetime.now())
        for var in variables.values():
            var.set("")

        variables["date_var"].set(datetime.now().strftime("%d/%m/%Y"))

    def validate_editing(self, selected_ids):
        """Validates if editing is possible (only one invoice selected)."""
        if len(selected_ids) != 1:
            show_warning(self, "Selecione exatamente uma nota para editar.")
            return False
        return True