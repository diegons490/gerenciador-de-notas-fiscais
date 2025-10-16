# gui/modules/invoice_add.py
"""
Module for managing the addition of new invoices.
Contains functions related to validation, formatting and saving of new invoices.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core import utils
from ..utils.popups import show_error, show_info


class InvoiceAddManager:
    """Manages the functionality of adding new invoices."""

    def __init__(self, database, theme_manager):
        self.database = database
        self.theme_manager = theme_manager

    def initialize_variables(self):
        """Initializes form variables."""
        return {
            "date_var": tk.StringVar(),
            "number_var": tk.StringVar(),
            "customer_var": tk.StringVar(),
            "value_var": tk.StringVar(),
            "phone_var": tk.StringVar(),
            "email_var": tk.StringVar(),
            "cnpj_var": tk.StringVar(),
            "address_var": tk.StringVar(),
        }

    def on_date_selected(self, date_entry, date_var, event=None):
        """Callback when a date is selected."""
        try:
            selected_date = date_entry.get_date()
            date_var.set(selected_date.strftime("%d/%m/%Y"))
        except Exception:
            pass

    def validate_invoice_number_wrapper(self, number_var, event=None):
        """Validates and formats invoice number."""
        current = number_var.get()
        if current and not current.isdigit():
            number_var.set(utils.clean_number(current))

    def format_value_wrapper(self, value_var, event=None):
        """Formats value during typing and ALWAYS repositions cursor at the end."""
        current = value_var.get()
        if current:
            formatted = utils.format_typing_value(current)
            if current != formatted:
                value_var.set(formatted)
                # SEMPRE move o cursor para o final
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def apply_value_format_wrapper(self, value_var, event=None):
        """Applies final value formatting when focus is lost."""
        current = value_var.get()
        if current:
            value_var.set(utils.apply_final_value_format(current))

    def format_phone_wrapper(self, phone_var, event=None):
        """Formats phone during typing and ALWAYS repositions cursor at the end."""
        current = phone_var.get()
        if current:
            formatted = utils.format_phone(current)
            if current != formatted:
                phone_var.set(formatted)
                # SEMPRE move o cursor para o final
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def validate_email_wrapper(self, email_var, widget, event=None):
        """Validates email when focus is lost."""
        email = email_var.get()
        if email and not utils.validate_email(email):
            widget.configure(bootstyle=DANGER)
        else:
            widget.configure(bootstyle=PRIMARY)

    def format_cnpj_wrapper(self, cnpj_var, event=None):
        """Formats CNPJ during typing and ALWAYS repositions cursor at the end."""
        current = cnpj_var.get()
        if current:
            formatted = utils.format_cnpj(current)
            if current != formatted:
                cnpj_var.set(formatted)
                # SEMPRE move o cursor para o final
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def validate_form(self, date, number, customer, value, phone="", email="", cnpj="", address=""):
        """Validates all form fields."""
        valid, message = utils.validate_invoice_form(date, number, customer, value)
        if not valid:
            return False, message

        if phone and not utils.validate_phone(phone):
            return False, "Telefone inválido! Use (00) 00000-0000 ou (00) 0000-0000"

        if email and not utils.validate_email(email):
            return False, "Email inválido!"

        if cnpj and not utils.validate_cnpj(cnpj):
            return False, "CNPJ inválido! Deve ter 14 dígitos."

        return True, "Formulário válido"

    def save_new_invoice(self, parent, date, number, customer, value, phone, email, cnpj, address):
        """Saves a new invoice in the database."""
        try:
            value_decimal = utils.convert_to_decimal(value)
            date_sql = utils.format_sql_date(date)

            success = self.database.insert_invoice(
                date_sql, number, customer, value_decimal, phone, email, cnpj, address
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

    def clear_fields(self, date_entry, variables):
        """Clears all form fields."""
        date_entry.set_date(datetime.now())
        for var in variables.values():
            var.set("")

        variables["date_var"].set(datetime.now().strftime("%d/%m/%Y"))