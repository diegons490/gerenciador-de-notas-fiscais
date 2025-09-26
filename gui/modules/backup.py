# gui/modules/backup.py
"""
Interface para gerenciamento de backups do banco notes.db usando ttkbootstrap.
Agora cria e restaura apenas o banco de dados, com feedback imediato na aplicação.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
import shutil
from pathlib import Path
from ..utils.file_browser import askopenfilename, asksaveasfilename
from ..utils.popups import show_error, show_info, ask_yes_no
from ..utils import (
    create_info_tooltip,
    create_warning_tooltip,
    create_success_tooltip,
)


class ConfigBackup(tb.Frame):
    """Gerencia backup e restauração do banco de dados como diálogo modal."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database
        self.db_path = self.database.db_file

    def handle_backup(self):
        """Abre o diálogo de gerenciamento de backup."""
        self.show_backup_dialog()

    def show_backup_dialog(self):
        """Exibe opções de backup: criar ou restaurar backup."""
        dialog = tb.Toplevel(self.parent)
        dialog.title("Gerenciamento de Backups")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Conteúdo
        content = tb.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        tb.Label(
            content,
            text="Gerenciamento de Backups",
            font=("Helvetica", 14, "bold"),
            bootstyle=PRIMARY,
        ).pack(pady=(0, 8))

        tb.Label(
            content,
            text="Escolha a operação desejada:",
            font=("Helvetica", 11),
        ).pack(pady=(0, 12))

        # Frame com botões empilhados verticalmente
        buttons_frame = tb.Frame(content)
        buttons_frame.pack(fill=tk.X, pady=(6, 0))

        # Botão: Criar Backup
        btn_create = tb.Button(
            buttons_frame,
            text="Criar Backup",
            bootstyle=SUCCESS,
            command=lambda: self._create_backup_confirm(dialog),
        )
        btn_create.pack(fill=tk.X, pady=6)
        create_success_tooltip(btn_create, "Cria um backup do banco de dados atual.")

        # Botão: Restaurar Backup
        btn_restore = tb.Button(
            buttons_frame,
            text="Restaurar Backup",
            bootstyle=WARNING,
            command=lambda: self._restore_backup_confirm(dialog),
        )
        btn_restore.pack(fill=tk.X, pady=6)
        create_warning_tooltip(
            btn_restore,
            "Restaura um backup existente do banco de dados.\nIsso substituirá os dados atuais!",
        )

        # Botão: Cancelar
        btn_cancel = tb.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
        )
        btn_cancel.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_cancel, "Voltar ao menu principal.")

        # Centralizar o diálogo
        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()

    def _create_backup_confirm(self, dialog):
        """Confirmação e criação de backup."""
        dialog.destroy()
        self.create_backup()

    def _restore_backup_confirm(self, dialog):
        """Confirmação e restauração de backup."""
        dialog.destroy()
        self.restore_backup()

    def create_backup(self):
        """Cria backup do banco de dados notes.db."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"backup_notes_{timestamp}.db"

        file_path = asksaveasfilename(
            parent=self.parent,
            title="Salvar Backup Como",
            initialfile=default_filename,
            filetypes=[("Banco de Dados SQLite", "*.db")],
        )

        if file_path:
            # Garantir extensão .db
            if not file_path.lower().endswith(".db"):
                file_path = f"{file_path}.db"

            try:
                shutil.copy2(self.db_path, file_path)
                show_info(
                    self.parent,
                    f"Backup criado com sucesso!\n\nArquivo: {file_path}",
                )
            except Exception as e:
                show_error(self.parent, f"Falha ao criar backup!\n{e}")

    def restore_backup(self):
        """Restaura backup do banco de dados notes.db e atualiza a aplicação."""
        file_path = askopenfilename(
            parent=self.parent,
            title="Selecionar Arquivo de Backup",
            filetypes=[("Banco de Dados SQLite", "*.db")],
        )

        if file_path:
            result = ask_yes_no(
                self.parent,
                "ATENÇÃO: Isso substituirá seus dados atuais!\n\n"
                "Tem certeza que deseja restaurar o backup?",
                title="CONFIRMAÇÃO DE RESTAURAÇÃO",
            )

            if result == "Sim":
                try:
                    # Substituir apenas o arquivo do banco de dados
                    shutil.copy2(file_path, self.db_path)

                    # Atualizar a view atual para refletir os dados
                    if hasattr(self.controller, "refresh_current_view"):
                        self.controller.refresh_current_view()

                    show_info(
                        self.parent,
                        "Backup restaurado com sucesso e dados atualizados!",
                    )
                except Exception as e:
                    show_error(self.parent, f"Falha ao restaurar backup!\n{e}")
