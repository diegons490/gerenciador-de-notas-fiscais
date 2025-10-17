# gui/modules/main_menu.py
"""
Main system interface - grid modularized version.
Agora usa funções centralizadas do utils.py para formatação.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from functools import partial
from ..keys import EventKeys
from ..utils.popups import show_error, show_info, show_warning
from ..utils import create_info_tooltip, create_success_tooltip
from ..modules.table_manager import TableManagerFactory
from ..modules.invoice_add import InvoiceAddManager
from ..modules.invoice_edit import InvoiceEditManager
from ..modules.invoice_delete import InvoiceDelete
from ..modules.invoice_export import InvoiceExport
from ..modules.backup import ConfigBackup


class MainMenu(ttk.Frame):
    """Main modularized view using grid."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

        # Initialize modules
        self.table_manager = TableManagerFactory.create_table_manager("invoices", database)
        self.add_manager = InvoiceAddManager(database, theme_manager)
        self.edit_manager = InvoiceEditManager(database, theme_manager)
        self.delete_module = InvoiceDelete(self, controller, theme_manager, database)
        self.export_module = InvoiceExport(self, controller, theme_manager, database)
        self.backup_module = ConfigBackup(self, controller, theme_manager, database)

        # Application state
        self.editing_id = None
        self.edit_mode = False
        self.variables = self.add_manager.initialize_variables()  # dict of StringVar
        self.buttons = {}

        # Search bar variable and widget (local implementation to avoid focus issues)
        self.search_var = tk.StringVar()
        self.search_entry = None  # created in create_search_bar
        self.btn_search_clear = None
        
        # Customer combobox (functionality absorbed from SearchManager)
        self.customer_combobox = None

        self.setup_ui()
        self._attach_traces()
        self.refresh_data()

    def setup_ui(self):
        """Sets up the entire user interface using grid."""
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configure MainMenu grid
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Configure main_container grid
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=0)  # title
        self.main_container.rowconfigure(1, weight=0)  # search
        self.main_container.rowconfigure(2, weight=1)  # table (expands)
        self.main_container.rowconfigure(3, weight=0)  # last invoice
        self.main_container.rowconfigure(4, weight=0)  # combobox
        self.main_container.rowconfigure(5, weight=0)  # form
        self.main_container.rowconfigure(6, weight=0)  # buttons

        self.create_title()
        self.create_search_bar()  # local implementation
        self.create_table()
        self.create_last_invoice_frame()  # below table
        self.create_customer_combobox()  # functionality absorbed from SearchManager
        self.create_form()
        self.create_buttons()

    def _attach_traces(self):
        """Attaches traces to keep 'clear' button states updated."""
        # Trace for search clear button
        self.search_var.trace_add("write", lambda *a: self.update_search_clear_state())

        # Traces for form fields -> enable/disable "Clear Fields" button
        # use v=var in lambda to avoid late binding
        for name, var in self.variables.items():
            var.trace_add("write", lambda *a, v=var: self.update_clear_fields_button_state())

    def create_title(self):
        """Creates the page title."""
        title_label = ttk.Label(
            self.main_container,
            text="Gerenciador de Notas Fiscais",
            font=("Helvetica", 20, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center",
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")

        # Ensure expansion for centering
        self.main_container.grid_columnconfigure(0, weight=1)

    def create_search_bar(self):
        """
        Creates the search bar locally.
        Reason: avoid Entry focus loss caused by external widget updates.
        """
        search_frame = ttk.Frame(self.main_container)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        lbl = ttk.Label(search_frame, text="Pesquisar nota:")
        lbl.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Local search entry (uses self.search_var)
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=50
        )
        self.search_entry.grid(row=0, column=1, sticky="ew")
        # KeyRelease to update table while typing
        self.search_entry.bind("<KeyRelease>", self.on_search)
        # Ensure initial focus on entry
        try:
            self.search_entry.focus_set()
        except Exception:
            pass

        # Clear button: erases entire string and restores table
        btn_clear = ttk.Button(
            search_frame,
            text="Limpar",
            command=self.clear_search,
            bootstyle="outline-warning",
            width=8,
        )
        btn_clear.grid(row=0, column=2, padx=(10, 0))
        self.btn_search_clear = btn_clear
        # initial state: disabled (empty)
        self.btn_search_clear.config(state=DISABLED)

    def create_table(self):
        """Creates the invoices table."""
        table_frame = self.table_manager.create_table(self.main_container)
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.table_manager.bind_selection_event(self.on_table_select)

    def create_last_invoice_frame(self):
        """Creates the frame to display the last added invoice."""
        self.last_invoice_frame = ttk.LabelFrame(
            self.main_container, text="Última Nota Fiscal Adicionada", bootstyle=WARNING
        )
        self.last_invoice_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10))
        self.last_invoice_frame.columnconfigure(0, weight=1)

        inner_frame = ttk.Frame(self.last_invoice_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1)

        self.last_invoice_labels = {
            "date": ttk.Label(inner_frame, text="Data: -", font=("Helvetica", 9)),
            "number": ttk.Label(inner_frame, text="Número: -", font=("Helvetica", 9)),
            "customer": ttk.Label(inner_frame, text="Cliente: -", font=("Helvetica", 9)),
            "value": ttk.Label(inner_frame, text="Valor: -", font=("Helvetica", 9)),
        }

        self.last_invoice_labels["date"].grid(row=0, column=0, sticky="w", padx=5)
        self.last_invoice_labels["number"].grid(row=0, column=1, sticky="w", padx=5)
        self.last_invoice_labels["customer"].grid(row=0, column=2, sticky="w", padx=5)
        self.last_invoice_labels["value"].grid(row=0, column=3, sticky="w", padx=5)

    def create_customer_combobox(self):
        """Creates the customer selection combobox (functionality absorbed from SearchManager)."""
        customer_frame = ttk.LabelFrame(
            self.main_container, text="Seleção Rápida de Cliente", bootstyle=SUCCESS
        )
        customer_frame.columnconfigure(1, weight=1)

        ttk.Label(customer_frame, text="Cliente Cadastrado:").grid(
            row=0, column=0, sticky="w", padx=(10, 5), pady=10
        )

        self.customer_combobox = ttk.Combobox(
            customer_frame, state="readonly", postcommand=self.load_customers
        )
        self.customer_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        self.customer_combobox.bind("<<ComboboxSelected>>", self.on_customer_selected)

        btn_clear = ttk.Button(
            customer_frame,
            text="Limpar Seleção",
            command=self.clear_customer_selection,
            bootstyle=SECONDARY,
            width=15,
        )
        btn_clear.grid(row=0, column=2, padx=(5, 10), pady=10)

        self.load_customers()
        customer_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    def load_customers(self):
        """Loads the customer list into the combobox (functionality absorbed from SearchManager)."""
        try:
            customers = self.database.get_all_customers()
            customer_names = [customer[1] for customer in customers]
            self.customer_combobox["values"] = customer_names
        except Exception as e:
            print(f"Error loading customers: {e}")

    def on_customer_selected(self, event):
        """Fills the fields when a customer is selected (functionality absorbed from SearchManager)."""
        customer_name = self.customer_combobox.get()
        if not customer_name:
            return

        try:
            customer = self.database.get_customer_by_name(customer_name)
            if customer:
                _, name, phone, email, cnpj, address = customer
                # CORREÇÃO: Usar os nomes corretos das variáveis em inglês
                self.variables["customer_var"].set(name or "")
                self.variables["phone_var"].set(phone or "")
                self.variables["email_var"].set(email or "")
                self.variables["cnpj_var"].set(cnpj or "")
                self.variables["address_var"].set(address or "")
                show_info(self, f"Dados do cliente '{name}' carregados com sucesso!")
        except Exception as e:
            show_error(self, f"Erro ao carregar dados do cliente: {e}")

    def clear_customer_selection(self):
        """Clears the customer selection (functionality absorbed from SearchManager)."""
        self.customer_combobox.set("")
        # CORREÇÃO: Usar os nomes corretos das variáveis em inglês
        for field in [
            "customer_var",
            "phone_var",
            "email_var",
            "cnpj_var",
            "address_var",
        ]:
            self.variables[field].set("")
        show_info(self, "Seleção de cliente limpa.")

    def create_form(self):
        """Creates the invoice form."""
        form_frame = ttk.LabelFrame(
            self.main_container, text="Adicionar/Editar Nota Fiscal", bootstyle=SUCCESS
        )
        form_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        form_frame.columnconfigure(0, weight=1)

        inner_frame = ttk.Frame(form_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1 if i in [1, 3] else 0)

        self.create_form_fields(inner_frame)

    def create_form_fields(self, parent):
        """Creates the form fields."""
        from core import utils

        # Emission Date
        ttk.Label(parent, text="Data Emissão*:").grid(
            row=0, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        self.date_entry = DateEntry(
            parent,
            dateformat="%d/%m/%Y",
            firstweekday=6,
            startdate=datetime.now(),
            bootstyle=PRIMARY,
        )
        self.date_entry.grid(row=0, column=1, sticky=EW, pady=5, padx=(0, 10))
        self.date_entry.bind(
            "<<DateEntrySelected>>",
            lambda e: self.add_manager.on_date_selected(
                self.date_entry, self.variables["date_var"]
            ),
        )
        self.variables["date_var"].set(datetime.now().strftime("%d/%m/%Y"))

        # Phone
        ttk.Label(parent, text="Telefone:").grid(
            row=0, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_phone = ttk.Entry(parent, textvariable=self.variables["phone_var"])
        entry_phone.grid(row=0, column=3, sticky=EW, pady=5)
        entry_phone.bind(
            "<KeyRelease>",
            lambda e: utils.format_with_cursor_reposition(
                self.variables["phone_var"], utils.format_phone, e
            ),
        )

        # Number
        ttk.Label(parent, text="Número*:").grid(
            row=1, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_number = ttk.Entry(parent, textvariable=self.variables["number_var"])
        entry_number.grid(row=1, column=1, sticky=EW, pady=5, padx=(0, 10))
        entry_number.bind(
            "<KeyRelease>",
            lambda e: self.add_manager.validate_invoice_number_wrapper(
                self.variables["number_var"]
            ),
        )

        # Email
        ttk.Label(parent, text="Email:").grid(
            row=1, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_email = ttk.Entry(parent, textvariable=self.variables["email_var"])
        entry_email.grid(row=1, column=3, sticky=EW, pady=5)
        entry_email.bind(
            "<FocusOut>",
            lambda e: utils.validate_email_with_style(
                self.variables["email_var"], entry_email, e
            ),
        )

        # Customer
        ttk.Label(parent, text="Cliente*:").grid(
            row=2, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_customer = ttk.Entry(parent, textvariable=self.variables["customer_var"])
        entry_customer.grid(row=2, column=1, sticky=EW, pady=5, padx=(0, 10))

        # CNPJ
        ttk.Label(parent, text="CNPJ:").grid(
            row=2, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_cnpj = ttk.Entry(parent, textvariable=self.variables["cnpj_var"])
        entry_cnpj.grid(row=2, column=3, sticky=EW, pady=5)
        entry_cnpj.bind(
            "<KeyRelease>",
            lambda e: utils.format_with_cursor_reposition(
                self.variables["cnpj_var"], utils.format_cnpj, e
            ),
        )

        # Value
        ttk.Label(parent, text="Valor (R$)*:").grid(
            row=3, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_value = ttk.Entry(parent, textvariable=self.variables["value_var"])
        entry_value.grid(row=3, column=1, sticky=EW, pady=5, padx=(0, 10))
        entry_value.bind(
            "<KeyRelease>",
            lambda e: utils.format_with_cursor_reposition(
                self.variables["value_var"], utils.format_typing_value, e
            ),
        )

        # Address
        ttk.Label(parent, text="Endereço:").grid(
            row=3, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_address = ttk.Entry(parent, textvariable=self.variables["address_var"])
        entry_address.grid(row=3, column=3, sticky=EW, pady=5)

    def create_buttons(self):
        """Creates the action buttons."""
        button_frame = ttk.Frame(self.main_container)
        button_frame.grid(row=6, column=0, sticky="ew", pady=20)
        button_frame.columnconfigure(0, weight=1)

        # Line 1
        line1 = ttk.Frame(button_frame)
        line1.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        line1.columnconfigure(0, weight=1)

        line1_inner = ttk.Frame(line1)
        line1_inner.grid(row=0, column=0)

        buttons_line1 = [
            (
                "Salvar Nota",
                SUCCESS,
                self.save_invoice,
                "Salvar nota fiscal no sistema.",
            ),
            (
                "Editar Nota",
                WARNING,
                self.edit_invoice,
                "Carregar nota selecionada para edição.",
            ),
            (
                "Excluir",
                DANGER,
                self.handle_delete_notes,
                "Excluir notas selecionadas.",
            ),
            (
                "Exportar",
                PRIMARY,
                self.handle_export_notes,
                "Exportar notas selecionadas para CSV.",
            ),
            (
                "Limpar Campos",
                "OUTLINE-WARNING",
                self.clear_fields,
                "Limpar campos do formulário.",
            ),
        ]

        for i, (text, style, command, tooltip) in enumerate(buttons_line1):
            btn = ttk.Button(
                line1_inner, text=text, command=command, bootstyle=style, width=15
            )
            btn.grid(row=0, column=i, padx=5)

            if style == SUCCESS:
                create_success_tooltip(btn, tooltip)
            else:
                create_info_tooltip(btn, tooltip)

            # Store references to important buttons
            if text == "Salvar Nota":
                self.buttons["btn_save"] = btn
            elif text == "Editar Nota":
                self.buttons["btn_edit"] = btn
            elif text == "Excluir":
                self.buttons["btn_delete"] = btn
            elif text == "Exportar":
                self.buttons["btn_export"] = btn
            elif text == "Limpar Campos":
                # store reference to control state
                self.buttons["btn_clear_fields"] = btn
                # start disabled (empty)
                btn.config(state=DISABLED)

        # Line 2
        line2 = ttk.Frame(button_frame)
        line2.grid(row=1, column=0, sticky="nsew")
        line2.columnconfigure(0, weight=1)

        line2_inner = ttk.Frame(line2)
        line2_inner.grid(row=0, column=0)

        buttons_line2 = [
            (
                "Cadastros",
                INFO,
                lambda: self.controller.handle_event(EventKeys.CUSTOMER_REGISTRATION),
                "Gerenciar cadastro de clientes.",
            ),
            (
                "Relatório",
                SECONDARY,
                lambda: self.controller.handle_event(EventKeys.REPORT),
                "Gerar relatório completo.",
            ),
            ("Backup", LIGHT, self.handle_backup, "Gerencia backups das notas."),
            (
                "Tema",
                "SUCCESS-OUTLINE",
                lambda: self.controller.handle_event(EventKeys.THEME),
                "Altera o tema da interface.",
            ),
            (
                "Sobre",
                "INFO-OUTLINE",
                self.show_about,
                "Sobre este projeto.",
            ),
            (
                "Sair",
                DARK,
                lambda: self.controller.handle_event(EventKeys.EXIT),
                "Sair do aplicativo.",
            ),
        ]

        for i, (text, style, command, tooltip) in enumerate(buttons_line2):
            btn = ttk.Button(
                line2_inner, text=text, command=command, bootstyle=style, width=12
            )
            btn.grid(row=0, column=i, padx=5)
            create_info_tooltip(btn, tooltip)

    def update_search_clear_state(self):
        """Enables/disables the search 'Clear' button based on content."""
        if self.btn_search_clear is None:
            return
        term = (self.search_var.get() or "").strip()
        state = NORMAL if term else DISABLED
        try:
            self.btn_search_clear.config(state=state)
        except Exception:
            pass

    def update_clear_fields_button_state(self):
        """Enables/disables the 'Clear Fields' button if there is any text in relevant form fields."""
        btn = self.buttons.get("btn_clear_fields")
        if btn is None:
            return

        # Ignore date, as date_var is usually automatically filled
        fields_to_check = [
            k for k in self.variables.keys() if k != "date_var"  # CORREÇÃO: date_var
        ]

        any_filled = any(
            (self.variables[k].get() or "").strip() for k in fields_to_check
        )

        state = NORMAL if any_filled else DISABLED
        try:
            btn.config(state=state)
        except Exception:
            pass    

    def update_last_invoice(self):
        """Updates the frame with the last invoice data."""
        last_invoice = self.database.get_last_invoice()

        if last_invoice:
            emission_date, number, customer, value = last_invoice
            from core import utils  # Import here to avoid circular imports

            self.last_invoice_labels["date"].config(text=f"Data: {emission_date}")
            self.last_invoice_labels["number"].config(text=f"Número: {number}")
            self.last_invoice_labels["customer"].config(text=f"Cliente: {customer}")
            self.last_invoice_labels["value"].config(
                text=f"Valor: {utils.format_currency(value)}"
            )
        else:
            for label in self.last_invoice_labels.values():
                label.config(text="-")

    def on_search(self, event=None):
        """Search handler.
        Uses self.search_var (local implementation) to avoid focus loss
        and ensure consistent 'Clear' button behavior.
        """
        term = (self.search_var.get() or "").strip()

        # Local filtering (functionality absorbed from SearchManager)
        try:
            if term:
                # Try to use database method first
                result = self.database.search_invoices_by_term(term)
                self.table_manager.filtered_data = result
            else:
                self.table_manager.filtered_data = self.table_manager.all_data.copy()
        except Exception:
            # Fallback to local filtering
            if term:
                lower = term.lower()
                filtered = [
                    row
                    for row in self.table_manager.all_data
                    if any(lower in (str(col) or "").lower() for col in row)
                ]
                self.table_manager.filtered_data = filtered
            else:
                self.table_manager.filtered_data = self.table_manager.all_data.copy()

        # Update table with filtered data
        self.table_manager.update_table_data(self.table_manager.filtered_data)

        # Clear table selection to avoid side effects
        try:
            self.table_manager.clear_selection()
            self.table_manager.selected_ids = []
        except Exception:
            pass

        # Restore focus/cursor to search_entry after update (avoids "leaving" the field)
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

        # update search clear button state (trace also handles it, but we ensure here)
        self.update_search_clear_state()

    def on_table_select(self, event=None):
        """Table selection handler."""
        self.table_manager.selected_ids = self.table_manager.get_selected_ids()
        self.update_button_states()

    def clear_search(self):
        """Clears the search: erases the entry, restores the table and focuses the field."""
        if self.search_var is not None:
            self.search_var.set("")
        # call on_search to update table (restore all data)
        self.on_search()
        # ensure focus on entry
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
        # button state will be updated via trace

    def update_button_states(self):
        """Updates button states based on selection."""
        has_selection = len(getattr(self.table_manager, "selected_ids", [])) > 0
        single_selection = len(getattr(self.table_manager, "selected_ids", [])) == 1

        # Update button states (some may not exist until create_buttons)
        try:
            self.buttons["btn_delete"].config(
                state=NORMAL if has_selection else DISABLED
            )
        except Exception:
            pass
        try:
            self.buttons["btn_export"].config(
                state=NORMAL if has_selection else DISABLED
            )
        except Exception:
            pass
        try:
            self.buttons["btn_edit"].config(
                state=NORMAL if single_selection else DISABLED
            )
        except Exception:
            pass

        # Configure edit/cancel button
        try:
            if self.edit_mode:
                self.buttons["btn_edit"].config(
                    text="Cancelar Edição",
                    bootstyle=DANGER,
                    command=self.cancel_edit,
                )
            else:
                self.buttons["btn_edit"].config(
                    text="Editar Nota", bootstyle=WARNING, command=self.edit_invoice
                )
        except Exception:
            pass

    def save_invoice(self):
        """Saves a new invoice or updates an existing one."""
        # CORREÇÃO: Usar os nomes corretos das variáveis em inglês
        data = {
            "date": self.variables["date_var"].get().strip(),
            "number": self.variables["number_var"].get().strip(),
            "customer": self.variables["customer_var"].get().strip(),
            "value": self.variables["value_var"].get().strip(),
            "phone": self.variables["phone_var"].get().strip(),
            "email": self.variables["email_var"].get().strip(),
            "cnpj": self.variables["cnpj_var"].get().strip(),
            "address": self.variables["address_var"].get().strip(),
        }

        valid, message = self.add_manager.validate_form(
            date=data["date"],
            number=data["number"],
            customer=data["customer"],
            value=data["value"],
            phone=data["phone"],
            email=data["email"],
            cnpj=data["cnpj"],
            address=data["address"],
        )

        if not valid:
            show_error(self, message)
            return

        try:
            if self.edit_mode and self.editing_id:
                success = self.edit_manager.update_existing_invoice(
                    self, self.editing_id, **data
                )
                if success:
                    self.edit_mode = False
                    self.editing_id = None
                    self.buttons["btn_save"].config(
                        text="Salvar Nota", bootstyle=SUCCESS
                    )
            else:
                success = self.add_manager.save_new_invoice(self, **data)
                if success:
                    self.update_last_invoice()

            if success:
                self.refresh_data()

        except Exception as e:
            show_error(self, f"Erro ao salvar nota: {str(e)}")

    def edit_invoice(self):
        """Loads an invoice for editing."""
        if len(getattr(self.table_manager, "selected_ids", [])) != 1:
            show_warning(self, "Selecione exatamente uma nota para editar.")
            return

        invoice_id = self.table_manager.selected_ids[0]
        success = self.edit_manager.load_invoice_for_editing(
            self, invoice_id, self.date_entry, self.variables, self.buttons["btn_save"]
        )

        if success:
            self.edit_mode = True
            self.editing_id = invoice_id
            self.update_button_states()

    def cancel_edit(self):
        """Cancels edit mode."""
        self.edit_manager.cancel_edit(
            self, self.date_entry, self.variables, self.buttons["btn_save"]
        )
        self.edit_mode = False
        self.editing_id = None
        self.update_button_states()

    def clear_fields(self):
        """Clears the form fields."""
        self.add_manager.clear_fields(self.date_entry, self.variables)
        self.edit_mode = False
        self.editing_id = None
        try:
            self.buttons["btn_save"].config(text="Salvar Nota", bootstyle=SUCCESS)
        except Exception:
            pass
        # clear fields button state will be updated by trace

    def handle_delete_notes(self):
        """Handler for note deletion."""
        selected_ids = getattr(self.table_manager, "selected_ids", [])
        total_notes = self.database.get_total_invoices()

        if total_notes == 0:
            show_error(self, "Nenhuma nota encontrada no sistema!")
            return

        if not selected_ids:
            show_error(self, "Nenhuma nota selecionada!")
            return

        self.delete_module.handle_delete(selected_ids)
        self.refresh_data()

    def handle_export_notes(self):
        """Handler for note export."""
        selected_ids = getattr(self.table_manager, "selected_ids", [])
        total_notes = self.database.get_total_invoices()

        if total_notes == 0:
            show_error(self, "Nenhuma nota encontrada no sistema!")
            return

        if not selected_ids:
            show_error(self, "Nenhuma nota selecionada!")
            return

        self.export_module.handle_export(selected_ids)

    def handle_backup(self):
        """Handler for backup."""
        self.backup_module.handle_backup()

    def refresh_data(self):
        """Refreshes the view data."""
        self.table_manager.all_data = self.database.get_all_invoices()
        self.table_manager.filtered_data = self.table_manager.all_data.copy()
        self.table_manager.update_table_data(self.table_manager.filtered_data)
        try:
            self.table_manager.clear_selection()
        except Exception:
            pass
        self.table_manager.selected_ids = []
        self.clear_fields()
        self.update_button_states()
        self.update_last_invoice()
        # Reload customers in combobox
        self.load_customers()
        # update states related to fields and search
        self.update_clear_fields_button_state()
        self.update_search_clear_state()

    def show_about(self):
        """Shows information about the project."""
        from ..utils.popups import ask_yes_no
        import webbrowser

        response = ask_yes_no(
            self,
            "Este é um projeto de código aberto desenvolvido para gerenciamento de notas fiscais.\n\n"
            "Gostaria de visitar o repositório oficial no GitHub para obter mais informações,\n"
            "ver o código-fonte ou contribuir com o projeto?",
            "Sobre o Projeto"
        )

        if response == "Sim":
            webbrowser.open("https://github.com/diegons490/gerenciador-de-notas-fiscais")