# gui/modules/invoice_export.py
"""
Interface for exporting invoices to CSV using ttkbootstrap.
Works as modal dialog with export options.
"""

import os
import platform
import subprocess
import tkinter as tk
from datetime import datetime
import traceback

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from ..utils.popups import show_info, show_warning, show_error, ask_yes_no
from ..utils.file_browser import asksaveasfilename
from ..utils.tooltips import create_info_tooltip
from core.utils import format_currency


class InvoiceExport(tb.Frame):
    """Manages exporting invoices to CSV."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

    def handle_export(self, selected_ids):
        """Processes invoice export with choice interface."""
        total_invoices = self.database.get_total_invoices()

        if total_invoices == 0:
            show_error(self.parent, "Nenhuma nota encontrada para exportação!")
            return

        if selected_ids:
            self.show_export_dialog(selected_ids)
        else:
            show_error(self.parent, "Nenhuma nota selecionada para exportação!")

    def show_export_dialog(self, selected_ids):
        """Shows export options: only selected or all."""
        dialog = tb.Toplevel(self.parent)
        dialog.title("Exportar Notas")
        dialog.transient(self.parent)
        dialog.grab_set()

        content = tb.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        tb.Label(
            content,
            text="Como deseja exportar as notas?",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 8))

        buttons_frame = tb.Frame(content)
        buttons_frame.pack(fill=tk.X, pady=(6, 0))

        btn_selected = tb.Button(
            buttons_frame,
            text="Exportar Notas Selecionadas",
            bootstyle=PRIMARY,
            command=lambda: self._export_selected_confirm(selected_ids, dialog),
        )
        btn_selected.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_selected, "Exportar apenas as notas selecionadas para CSV.")

        btn_all = tb.Button(
            buttons_frame,
            text="Exportar Todas as Notas",
            bootstyle=INFO,
            command=lambda: self._export_all_confirm(dialog),
        )
        btn_all.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_all, "Exportar todas as notas do sistema para CSV.")

        btn_cancel = tb.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
        )
        btn_cancel.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_cancel, "Cancelar a exportação de notas.")

        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()

    def _export_selected_confirm(self, selected_ids, dialog):
        """Exports selected invoices."""
        dialog.destroy()
        self.export_invoices(selected_ids, "selecionadas")

    def _export_all_confirm(self, dialog):
        """Exports all system invoices."""
        dialog.destroy()
        all_invoices = self.database.get_all_invoices()
        ids = [n[0] for n in all_invoices]
        self.export_invoices(ids, "todas")

    def export_invoices(self, invoice_ids, export_type):
        """Exports invoices to CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"notas_{export_type}_{timestamp}.csv"

        try:
            file_path = asksaveasfilename(
                parent=self.parent,
                title="Salvar CSV",
                initialfile=default_filename,
                filetypes=[("Arquivos CSV", "*.csv")],
            )
        except Exception as e:
            show_error(self.parent, f"Erro ao abrir diálogo de salvar: {str(e)}")
            return

        if not file_path:
            return

        if not file_path.lower().endswith(".csv"):
            file_path = f"{file_path}.csv"

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                # ALTERAÇÃO: Usar ponto e vírgula como separador
                f.write("Data Emissao;Numero;Cliente;Valor;Telefone;Email;CNPJ;Endereço\n")

                for invoice_id in invoice_ids:
                    invoice = self.database.get_invoice_by_id(invoice_id)
                    if not invoice:
                        continue
                    
                    date, number, customer, value, phone, email, cnpj, address = invoice
                    
                    # CORREÇÃO: Garantir formatação sempre com duas casas decimais
                    # Converter para float primeiro
                    if isinstance(value, (int, float)):
                        value_float = float(value)
                    else:
                        # Se for string, limpar e converter
                        value_clean = str(value).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        value_float = float(value_clean) if value_clean else 0.0
                    
                    # Formatar com SEMPRE duas casas decimais
                    # Primeiro formatar como float com 2 casas
                    value_str = f"{value_float:.2f}"
                    # Substituir ponto por vírgula para formato brasileiro
                    value_str = value_str.replace('.', ',')
                    # Adicionar separadores de milhar se necessário
                    parts = value_str.split(',')
                    integer_part = parts[0]
                    decimal_part = parts[1] if len(parts) > 1 else "00"
                    
                    # Adicionar separadores de milhar
                    if len(integer_part) > 3:
                        integer_part = f"{int(integer_part):,}".replace(",", ".")
                    
                    value_formatted = f"{integer_part},{decimal_part}"
                    
                    # Garantir que campos vazios sejam exportados como string vazia
                    phone = phone or ""
                    email = email or ""
                    cnpj = cnpj or ""
                    address = address or ""
                    
                    # ALTERAÇÃO: Usar ponto e vírgula como separador
                    line = f'{date};{number};"{customer}";"{value_formatted}";"{phone}";"{email}";"{cnpj}";"{address}"\n'
                    f.write(line)

            show_info(
                self.parent, 
                f"Exportação concluída!\n\n"
                f"Arquivo salvo em:\n{file_path}\n\n"
                f"Total de notas exportadas: {len(invoice_ids)}"
            )

            open_file = ask_yes_no(
                self.parent, 
                "Deseja abrir o arquivo no editor de planilhas padrão?"
            )
            if open_file == "Sim":
                self.open_file_in_system(file_path)

        except Exception as e:
            show_error(self.parent, f"Erro ao exportar arquivo: {str(e)}")

    def open_file_in_system(self, file_path):
        """Opens file in system's default application."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.Popen(["open", file_path])
            else:
                try:
                    subprocess.Popen(["xdg-open", file_path])
                except Exception:
                    try:
                        subprocess.Popen(["gio", "open", file_path])
                    except Exception as e:
                        show_warning(self.parent, f"Não foi possível abrir automaticamente:\n{str(e)}")
        except Exception as e:
            show_warning(self.parent, f"Erro ao tentar abrir o arquivo:\n{str(e)}")