# gui/modules/customer_registration.py
"""
Complete interface for customer registration and management using ttkbootstrap.
Agora usa funções centralizadas do utils.py para formatação.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from core import utils
from ..keys import EventKeys
from ..utils.popups import ask_yes_no, show_info, show_error
from ..utils.tooltips import create_info_tooltip, create_warning_tooltip, create_error_tooltip, create_success_tooltip
from ..modules.table_manager import TableManagerFactory


class CustomerRegistration(tb.Frame):
    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

        self.table_manager = TableManagerFactory.create_table_manager("customers", database)
        self.selected_ids = []
        self.all_customers = []
        self.filtered_customers = []
        self.editing_id = None
        self.edit_mode = False

        self.search_entry = None
        self.btn_search_clear = None
        self.btn_save = None
        self.btn_edit = None
        self.btn_clear_fields = None

        self.initialize_variables()
        self.create_widgets()
        self._attach_traces()
        self.refresh_data()

    def initialize_variables(self):
        """Initialize form variables."""
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.cnpj_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.search_var = tk.StringVar()

    def _attach_traces(self):
        """Attaches traces to update button states."""
        self.search_var.trace_add("write", lambda *a: self.update_search_clear_state())
        for var in (self.name_var, self.phone_var, self.email_var, self.cnpj_var, self.address_var):
            var.trace_add("write", lambda *a: self.update_clear_fields_state())

    def create_widgets(self):
        """Creates all widgets."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = tb.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = tb.Label(
            main_frame,
            text="Cadastro e Gerenciamento de Clientes",
            font=("Helvetica", 18, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center",
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        main_frame.grid_columnconfigure(0, weight=1)

        self.create_search_bar(main_frame)
        self.create_customers_list(main_frame)
        self.create_last_customer_frame(main_frame)
        self.create_form(main_frame)
        self.create_action_buttons(main_frame)

    def create_search_bar(self, parent):
        """Creates search bar."""
        search_frame = tb.Frame(parent)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        tb.Label(search_frame, text="Pesquisar cliente:").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )

        self.search_entry = tb.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        try:
            self.search_entry.focus_set()
        except Exception:
            pass

        btn_clear = tb.Button(
            search_frame,
            text="Limpar",
            command=self.clear_search,
            bootstyle="outline-warning",
            width=8,
        )
        btn_clear.grid(row=0, column=2, padx=(10, 0))
        self.btn_search_clear = btn_clear
        self.btn_search_clear.config(state=DISABLED)

    def create_customers_list(self, parent):
        """Creates customers table."""
        table_frame = self.table_manager.create_table(parent)
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.table_manager.bind_selection_event(self.on_table_select)

    def create_last_customer_frame(self, parent):
        """Creates last customer display frame."""
        self.last_customer_frame = tb.LabelFrame(
            parent, text="Último Cliente Cadastrado", bootstyle=WARNING
        )
        self.last_customer_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10))
        self.last_customer_frame.columnconfigure(0, weight=1)

        inner_frame = tb.Frame(self.last_customer_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1)

        self.last_customer_labels = {
            "name": tb.Label(inner_frame, text="Nome: -", font=("Helvetica", 9)),
            "phone": tb.Label(inner_frame, text="Telefone: -", font=("Helvetica", 9)),
            "email": tb.Label(inner_frame, text="Email: -", font=("Helvetica", 9)),
            "cnpj": tb.Label(inner_frame, text="CNPJ: -", font=("Helvetica", 9)),
        }

        self.last_customer_labels["name"].grid(row=0, column=0, sticky="w", padx=5)
        self.last_customer_labels["phone"].grid(row=0, column=1, sticky="w", padx=5)
        self.last_customer_labels["email"].grid(row=0, column=2, sticky="w", padx=5)
        self.last_customer_labels["cnpj"].grid(row=0, column=3, sticky="w", padx=5)

    def create_form(self, parent):
        """Creates customer form."""
        form_frame = tb.LabelFrame(parent, text="Cadastrar/Editar Cliente", bootstyle=SUCCESS)
        form_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Nome*:", self.name_var, 0),
            ("Telefone:", self.phone_var, 1),
            ("Email:", self.email_var, 2),
            ("CNPJ:", self.cnpj_var, 3),
            ("Endereço:", self.address_var, 4),
        ]

        for i, (label, var, row) in enumerate(fields):
            lbl = tb.Label(form_frame, text=label)
            lbl.grid(row=row, column=0, sticky="w", pady=5, padx=10)

            entry = tb.Entry(form_frame, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=10)

            if label == "Telefone:":
                entry.bind(
                    "<KeyRelease>",
                    lambda e, v=var: utils.format_with_cursor_reposition(
                        v, utils.format_phone, e
                    ),
                )
                create_info_tooltip(entry, "Telefone do cliente (formato: (00) 00000-0000).")
            elif label == "Email:":
                entry.bind(
                    "<FocusOut>",
                    lambda e, v=var, w=entry: utils.validate_email_with_style(v, w, e),
                )
                create_info_tooltip(entry, "Email do cliente (exemplo@dominio.com).")
            elif label == "CNPJ:":
                entry.bind(
                    "<KeyRelease>",
                    lambda e, v=var: utils.format_with_cursor_reposition(
                        v, utils.format_cnpj, e
                    ),
                )
                create_info_tooltip(entry, "CNPJ do cliente (00.000.000/0000-00).")
            else:
                create_info_tooltip(entry, f"{label.replace(':', '')} do cliente.")

    def create_action_buttons(self, parent):
        """Creates action buttons."""
        button_frame = tb.Frame(parent)
        button_frame.grid(row=5, column=0, sticky="ew", pady=20)
        button_frame.grid_columnconfigure(0, weight=1)

        btn_container = tb.Frame(button_frame)
        btn_container.grid(row=0, column=0)

        buttons = [
            ("Salvar Cliente", self.save_customer, SUCCESS, "Salvar cliente no sistema.", 0),
            ("Editar Cliente", self.edit_customer, WARNING, "Editar cliente selecionado.", 1),
            ("Excluir", self.delete_customers_choice, DANGER, "Excluir clientes selecionados.", 2),
            ("Limpar Campos", self.clear_fields, "outline-warning", "Limpar campos do formulário.", 3),
            ("Voltar ao Menu", lambda: self.controller.handle_event(EventKeys.BACK), OUTLINE, "Voltar ao menu principal.", 4),
        ]

        for text, command, style, tooltip, col in buttons:
            btn = tb.Button(btn_container, text=text, command=command, bootstyle=style, width=15)
            btn.grid(row=0, column=col, padx=5)

            if style == SUCCESS:
                create_success_tooltip(btn, tooltip)
            elif style == WARNING:
                create_warning_tooltip(btn, tooltip)
            elif style == DANGER:
                create_error_tooltip(btn, tooltip)
            else:
                create_info_tooltip(btn, tooltip)

            if text == "Salvar Cliente":
                self.btn_save = btn
            elif text == "Editar Cliente":
                self.btn_edit = btn
            elif text == "Limpar Campos":
                self.btn_clear_fields = btn
                self.btn_clear_fields.config(state=DISABLED)

        try:
            self.btn_edit.config(state=DISABLED)
        except Exception:
            pass

    def update_search_clear_state(self):
        """Enables/disables the search clear button."""
        if self.btn_search_clear is None:
            return
        term = (self.search_var.get() or "").strip()
        state = NORMAL if term else DISABLED
        try:
            self.btn_search_clear.config(state=state)
        except Exception:
            pass

    def update_clear_fields_state(self):
        """Enables/disables the 'Clear Fields' button if any form field has text."""
        btn = getattr(self, "btn_clear_fields", None)
        if btn is None:
            return
        any_filled = any(
            (v.get() or "").strip()
            for v in (self.name_var, self.phone_var, self.email_var, self.cnpj_var, self.address_var)
        )
        try:
            btn.config(state=NORMAL if any_filled else DISABLED)
        except Exception:
            pass

    def update_last_customer(self):
        """Updates the frame with the last registered customer data."""
        all_customers = self.database.get_all_customers()

        if all_customers:
            last_customer = all_customers[0] if all_customers else None

            if last_customer and len(last_customer) >= 6:
                customer_id, name, phone, email, cnpj, address = last_customer

                self.last_customer_labels["name"].config(text=f"Nome: {name}")
                self.last_customer_labels["phone"].config(text=f"Telefone: {phone or '-'}")
                self.last_customer_labels["email"].config(text=f"Email: {email or '-'}")
                self.last_customer_labels["cnpj"].config(text=f"CNPJ: {cnpj or '-'}")
            else:
                self.clear_last_customer_labels()
        else:
            self.clear_last_customer_labels()

    def clear_last_customer_labels(self):
        """Clears the last customer labels."""
        for label in self.last_customer_labels.values():
            label.config(text="-")

    def on_search(self, event=None):
        """Handler for search. Uses self.search_var to avoid focus loss."""
        term = (self.search_var.get() or "").strip()

        try:
            if term:
                if hasattr(self.database, "search_customers"):
                    self.filtered_customers = self.database.search_customers(term)
                else:
                    lower = term.lower()
                    self.filtered_customers = [
                        row
                        for row in self.all_customers
                        if any(lower in (str(col) or "").lower() for col in row)
                    ]
            else:
                self.filtered_customers = self.all_customers[:]
        except Exception:
            if term:
                lower = term.lower()
                self.filtered_customers = [
                    row
                    for row in self.all_customers
                    if any(lower in (str(col) or "").lower() for col in row)
                ]
            else:
                self.filtered_customers = self.all_customers[:]

        try:
            self.table_manager.update_table_data(self.filtered_customers)
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao atualizar tabela de clientes: {e}")

        try:
            self.table_manager.clear_selection()
            if hasattr(self.table_manager, "selected_ids"):
                self.table_manager.selected_ids = []
        except Exception:
            pass

        # Restore focus/cursor to search_entry after update
        if self.search_entry:
            try:
                self.search_entry.after_idle(
                    lambda: (
                        self.search_entry.focus_set(),
                        self.search_entry.icursor(tk.END),
                    )
                )
            except Exception:
                pass

        # Update search clear button state
        self.update_search_clear_state()

    def clear_search(self):
        """Clears search: empties entry, restores table and focuses field."""
        try:
            self.search_var.set("")
        except Exception:
            pass

        self.on_search()

        # Ensure focus on entry
        if self.search_entry:
            try:
                self.search_entry.after_idle(
                    lambda: (
                        self.search_entry.focus_set(),
                        self.search_entry.icursor(tk.END),
                    )
                )
            except Exception:
                pass

    def on_table_select(self, event=None):
        """Handler for table selection."""
        self.selected_ids = self.table_manager.get_selected_ids()
        self.update_buttons_state()

    def refresh_data(self):
        """Refreshes all data in the view."""
        self.all_customers = self.database.get_all_customers()
        self.filtered_customers = self.all_customers[:]
        self.selected_ids = []
        self.edit_mode = False
        self.editing_id = None
        self.update_table()
        self.clear_fields()
        self.update_buttons_state()
        self.update_last_customer()
        # Update states
        self.update_clear_fields_state()
        self.update_search_clear_state()

    def update_table(self):
        """Updates the table with current data."""
        try:
            self.table_manager.update_table_data(self.filtered_customers)
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao atualizar tabela de clientes: {e}")

    def update_buttons_state(self):
        """Updates button states based on selection and edit mode."""
        has_selection = len(self.selected_ids) > 0
        single_selection = len(self.selected_ids) == 1

        try:
            if hasattr(self, 'btn_edit'):
                if self.edit_mode:
                    self.btn_edit.config(
                        state=NORMAL,
                        text="Cancelar Edição",
                        bootstyle=DANGER,
                        command=self.cancel_editing,
                    )
                    # Edit mode: change Save button to Update
                    self.btn_save.config(
                        text="Atualizar Cliente",
                        bootstyle=WARNING,
                        command=self.save_customer,
                    )
                    create_warning_tooltip(self.btn_save, "Atualizar cliente editado.")
                else:
                    self.btn_edit.config(
                        state=NORMAL if single_selection else DISABLED,
                        text="Editar Cliente",
                        bootstyle=WARNING,
                        command=self.edit_customer,
                    )
                    self.btn_save.config(
                        text="Salvar Cliente",
                        bootstyle=SUCCESS,
                        command=self.save_customer,
                    )
                    create_success_tooltip(self.btn_save, "Salvar cliente no sistema.")
        except Exception:
            pass

    def delete_customers_choice(self):
        """Shows delete options dialog."""
        total_customers = self.database.get_total_customers()

        if total_customers == 0:
            show_error(self.winfo_toplevel(), "Não há clientes no sistema!")
            return

        if not self.selected_ids:
            show_error(self.winfo_toplevel(), "Nenhum cliente selecionado para exclusão!")
            return

        parent = self.winfo_toplevel()
        dialog = tb.Toplevel(parent)
        dialog.title("Excluir Clientes")
        dialog.transient(parent)
        dialog.grab_set()

        content = tb.Frame(dialog, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        tb.Label(
            content,
            text="Como deseja excluir os clientes?",
            font=("Helvetica", 14, "bold"),
        ).grid(row=0, column=0, pady=(0, 8))

        buttons_frame = tb.Frame(content)
        buttons_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)

        dialog_buttons = [
            (
                "Apenas Selecionados",
                WARNING,
                lambda: self._delete_selected_confirm(self.selected_ids, dialog),
            ),
            ("Todos os Clientes", DANGER, lambda: self._confirm_and_delete_all(dialog)),
            ("Cancelar", SECONDARY, dialog.destroy),
        ]

        for i, (text, style, command) in enumerate(dialog_buttons):
            btn = tb.Button(buttons_frame, text=text, bootstyle=style, command=command)
            btn.grid(row=i, column=0, sticky="ew", pady=6)

        dialog.update_idletasks()
        w, h = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()

    def _delete_selected_confirm(self, selected_ids, dialog):
        """Deletes selected customers."""
        try:
            for customer_id in selected_ids:
                self.database.delete_customer(customer_id)
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao excluir clientes: {e}")
            dialog.destroy()
            return

        dialog.destroy()
        show_info(self.winfo_toplevel(), f"{len(selected_ids)} cliente(s) excluído(s) com sucesso!")
        self.refresh_data()

    def _confirm_and_delete_all(self, dialog):
        """Confirms and deletes all customers."""
        total = self.database.get_total_customers()
        msg = f"ATENÇÃO: Esta ação excluirá TODOS os {total} cliente(s) do sistema!\n\nEsta operação NÃO pode ser desfeita.\n\nDeseja realmente prosseguir?"

        resposta = ask_yes_no(self.winfo_toplevel(), msg, title="CONFIRMAÇÃO PERIGOSA")

        if resposta == "Sim":
            try:
                self.database.delete_all_customers()
            except Exception as e:
                dialog.destroy()
                show_error(self.winfo_toplevel(), f"Erro ao excluir todos os clientes: {e}")
                return

            dialog.destroy()
            show_info(self.winfo_toplevel(), f"Todas as {total} cliente(s) foram excluídas com sucesso!")
            self.refresh_data()

    def save_customer(self):
        """Saves or updates a customer."""
        valid, message = utils.validate_customer_form(
            self.name_var.get().strip(),
            self.phone_var.get().strip(),
            self.email_var.get().strip(),
            self.cnpj_var.get().strip(),
        )

        if not valid:
            show_error(self.winfo_toplevel(), message)
            return

        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        cnpj = self.cnpj_var.get().strip()
        address = self.address_var.get().strip()

        try:
            if self.edit_mode and self.editing_id:
                success = self.database.update_customer(
                    self.editing_id, name, phone, email, cnpj, address
                )
                if success:
                    show_info(self.winfo_toplevel(), "Cliente atualizado com sucesso!")
                    self.edit_mode = False
                    self.editing_id = None
                    self.update_buttons_state()
                else:
                    show_error(
                        self.winfo_toplevel(),
                        "Erro ao atualizar cliente! Verifique se o nome já existe.",
                    )
            else:
                success = self.database.insert_customer(name, phone, email, cnpj, address)
                if success:
                    show_info(self.winfo_toplevel(), "Cliente cadastrado com sucesso!")
                    self.update_last_customer()
                else:
                    show_error(self.winfo_toplevel(), "Já existe um cliente com este nome!")

            self.refresh_data()
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao salvar cliente: {str(e)}")

    def edit_customer(self):
        """Loads a customer for editing."""
        if not self.selected_ids or len(self.selected_ids) != 1:
            show_error(self.winfo_toplevel(), "Selecione exatamente um cliente para edição!")
            return

        customer_id = self.selected_ids[0]
        customer = self.database.get_customer_by_id(customer_id)

        if customer:
            customer_id, name, phone, email, cnpj, address = customer
            self.name_var.set(name or "")
            self.phone_var.set(phone or "")
            self.email_var.set(email or "")
            self.cnpj_var.set(cnpj or "")
            self.address_var.set(address or "")

            self.edit_mode = True
            self.editing_id = customer_id
            self.update_buttons_state()
            show_info(
                self.winfo_toplevel(),
                "Cliente carregado para edição. Modifique os campos e clique em Atualizar.",
            )

    def cancel_editing(self):
        """Cancels edit mode."""
        self.edit_mode = False
        self.editing_id = None
        self.clear_fields()
        self.update_buttons_state()
        show_info(self.winfo_toplevel(), "Edição cancelada. Campos limpos.")

    def clear_fields(self):
        """Clears all form fields."""
        self.name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.cnpj_var.set("")
        self.address_var.set("")
        self.edit_mode = False
        self.editing_id = None
        self.update_buttons_state()