# gui/modules/invoice_delete.py
"""
Interface for deleting invoices using ttkbootstrap.
Includes tooltips and categorized confirmations.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..utils.popups import ask_yes_no, show_info, show_error
from ..utils.tooltips import create_warning_tooltip, create_error_tooltip, create_info_tooltip
from ..keys import EventKeys


class InvoiceDelete(ttk.Frame):
    """Manages invoice deletion."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

    def handle_delete(self, selected_ids):
        """Processes invoice deletion with choice interface."""
        total_invoices = self.database.get_total_invoices()

        if total_invoices == 0:
            show_error(self.parent, "Nenhuma nota encontrada para exclusão!")
            return

        if selected_ids:
            self.show_delete_dialog(selected_ids)
        else:
            show_error(self.parent, "Nenhuma nota selecionada para exclusão!")

    def show_delete_dialog(self, selected_ids):
        """Shows deletion options: only selected or all."""
        dialog = ttk.Toplevel(self.parent)
        dialog.title("Excluir Notas")
        dialog.transient(self.parent)
        dialog.grab_set()

        content = ttk.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            content,
            text="Como deseja excluir as notas?",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 8))

        buttons_frame = ttk.Frame(content)
        buttons_frame.pack(fill=tk.X, pady=(6, 0))

        btn_selected = ttk.Button(
            buttons_frame,
            text="Apenas Selecionadas",
            bootstyle=WARNING,
            command=lambda: self._delete_selected_confirm(selected_ids, dialog),
        )
        btn_selected.pack(fill=tk.X, pady=6)
        create_warning_tooltip(btn_selected, "Excluir apenas as notas selecionadas.")

        btn_all = ttk.Button(
            buttons_frame,
            text="Todas as Notas",
            bootstyle=DANGER,
            command=lambda: self._confirm_and_delete_all(dialog),
        )
        btn_all.pack(fill=tk.X, pady=6)
        create_error_tooltip(btn_all, "Excluir todas as notas do sistema (irreversível).")

        btn_cancel = ttk.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
        )
        btn_cancel.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_cancel, "Cancelar a exclusão de notas.")

        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()

    def _delete_selected_confirm(self, selected_ids, dialog):
        """Deletes selected invoices."""
        try:
            for invoice_id in selected_ids:
                self.database.delete_invoice(invoice_id)
        except Exception as e:
            show_error(self.parent, f"Erro ao excluir notas: {e}")
            dialog.destroy()
            return

        dialog.destroy()
        show_info(self.parent, f"{len(selected_ids)} nota(s) excluída(s) com sucesso!")
        self._refresh_view()

    def _confirm_and_delete_all(self, dialog):
        """Shows danger confirmation and deletes all invoices if confirmed."""
        total = self.database.get_total_invoices()
        msg = (
            f"ATENÇÃO: Esta ação excluirá TODAS as {total} nota(s) do sistema!\n\n"
            "Esta operação NÃO pode ser desfeita.\n\n"
            "Deseja realmente prosseguir?"
        )

        resposta = ask_yes_no(self.parent, msg, title="CONFIRMAÇÃO PERIGOSA")

        if resposta == "Sim":
            try:
                self.database.delete_all_invoices()
            except Exception as e:
                dialog.destroy()
                show_error(self.parent, f"Erro ao excluir todas as notas: {e}")
                return

            dialog.destroy()
            show_info(self.parent, f"Todas as {total} nota(s) foram excluídas com sucesso!")
            self._refresh_view()

    def _refresh_view(self):
        """Refreshes the main view."""
        try:
            self.controller.refresh_main_menu()
        except Exception:
            try:
                self.controller.handle_event(EventKeys.REFRESH)
            except Exception:
                pass