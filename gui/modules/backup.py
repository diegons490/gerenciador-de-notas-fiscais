# gui/modules/backup.py
"""
Interface para gerenciamento de backups dos bancos de dados usando ttkbootstrap.
Agora cria e restaura backups de invoices.db e customers.db em um arquivo ZIP.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
import shutil
import zipfile
from pathlib import Path
from ..utils.file_browser import askopenfilename, asksaveasfilename
from ..utils.popups import show_error, show_info, ask_yes_no
from ..utils import (
    create_info_tooltip,
    create_warning_tooltip,
    create_success_tooltip,
)


class ConfigBackup(tb.Frame):
    """Gerencia backup e restauração dos bancos de dados como diálogo modal."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database
        self.invoices_db_path = self.database.db_file
        self.customers_db_path = self.database.customer_db_file
        self.data_dir = self.database.data_dir

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
        create_success_tooltip(btn_create, "Cria um backup completo dos bancos de dados (invoices.db e customers.db).")

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
            "Restaura um backup existente dos bancos de dados.\nIsso substituirá os dados atuais!",
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
        """Cria backup dos bancos de dados em um arquivo ZIP."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # CORREÇÃO: Nome do arquivo atualizado para backup_GNF_timestamp.zip
        default_filename = f"backup_GNF_{timestamp}.zip"

        file_path = asksaveasfilename(
            parent=self.parent,
            title="Salvar Backup Como",
            initialfile=default_filename,
            filetypes=[("Arquivo ZIP", "*.zip")],
        )

        if file_path:
            # Garantir extensão .zip
            if not file_path.lower().endswith(".zip"):
                file_path = f"{file_path}.zip"

            try:
                # Verificar se os arquivos de banco de dados existem
                if not self.invoices_db_path.exists():
                    show_error(self.parent, "Arquivo invoices.db não encontrado!")
                    return
                
                if not self.customers_db_path.exists():
                    show_error(self.parent, "Arquivo customers.db não encontrado!")
                    return

                # Criar arquivo ZIP
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Adicionar ambos os bancos de dados ao ZIP
                    zipf.write(self.invoices_db_path, "invoices.db")
                    zipf.write(self.customers_db_path, "customers.db")
                    
                    # Adicionar informações do backup
                    info_content = f"""Backup criado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Sistema: Gerenciador de Notas Fiscais
Arquivos incluídos:
- invoices.db (Notas Fiscais)
- customers.db (Clientes)"""
                    
                    zipf.writestr("backup_info.txt", info_content)

                show_info(
                    self.parent,
                    f"Backup criado com sucesso!\n\n"
                    f"Arquivo: {file_path}\n"
                    f"Contém: invoices.db e customers.db",
                )
            except Exception as e:
                show_error(self.parent, f"Falha ao criar backup!\n{str(e)}")

    def restore_backup(self):
        """Restaura backup dos bancos de dados a partir de um arquivo ZIP."""
        file_path = askopenfilename(
            parent=self.parent,
            title="Selecionar Arquivo de Backup",
            filetypes=[("Arquivo ZIP", "*.zip")],
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
                    # Verificar se o arquivo ZIP é válido
                    if not zipfile.is_zipfile(file_path):
                        show_error(self.parent, "Arquivo ZIP inválido!")
                        return

                    # Extrair arquivos temporariamente
                    temp_dir = self.data_dir / "temp_restore"
                    temp_dir.mkdir(exist_ok=True)

                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        # Verificar se os arquivos necessários estão no ZIP
                        file_list = zipf.namelist()
                        if "invoices.db" not in file_list or "customers.db" not in file_list:
                            show_error(
                                self.parent,
                                "Arquivo ZIP não contém os bancos de dados necessários!\n"
                                "Certifique-se de que o backup contenha invoices.db e customers.db"
                            )
                            return
                        
                        # Extrair arquivos
                        zipf.extractall(temp_dir)

                    # CORREÇÃO: Removido o backup automático dos arquivos atuais
                    # Substituir diretamente os arquivos atuais
                    shutil.copy2(temp_dir / "invoices.db", self.invoices_db_path)
                    shutil.copy2(temp_dir / "customers.db", self.customers_db_path)

                    # Limpar diretório temporário
                    shutil.rmtree(temp_dir)

                    # Atualizar a view atual para refletir os dados
                    if hasattr(self.controller, "refresh_current_view"):
                        self.controller.refresh_current_view()

                    show_info(
                        self.parent,
                        "Backup restaurado com sucesso!\n\n"
                        "Dados atualizados:\n"
                        "- Notas fiscais\n"
                        "- Clientes",
                    )
                except Exception as e:
                    show_error(self.parent, f"Falha ao restaurar backup!\n{str(e)}")

    def verify_backup_files(self, zip_path):
        """Verifica se o arquivo ZIP contém os arquivos necessários."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                return "invoices.db" in file_list and "customers.db" in file_list
        except Exception:
            return False