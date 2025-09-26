# gui/modules/export_note.py
"""
Interface para exportação de notas fiscais em CSV usando ttkbootstrap.
Funciona exatamente como DeleteNotes: diálogo modal com opções de exportação.
"""

import os
import platform
import subprocess
import tkinter as tk
from datetime import datetime
import traceback

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from ..utils import (
    show_info,
    show_warning,
    show_error,
    ask_yes_no,
    asksaveasfilename,
    create_info_tooltip,
    create_warning_tooltip,
    create_error_tooltip,
)

from core.utils import formatar_moeda
from ..keys import EventKeys


class ExportNotes(tb.Frame):
    """Gerencia exportação de notas fiscais para CSV."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

    def handle_export(self, selected_ids):
        """Processa exportação das notas com interface de escolha."""
        total_notas = self.database.get_total_notas()

        if total_notas == 0:
            show_error(self.parent, "Nenhuma nota encontrada para exportação!")
            return

        if selected_ids:
            self.show_export_dialog(selected_ids)
        else:
            show_error(self.parent, "Nenhuma nota selecionada para exportação!")

    def show_export_dialog(self, selected_ids):
        """Exibe opções de exportação: apenas selecionadas ou todas."""
        dialog = tb.Toplevel(self.parent)
        dialog.title("Exportar Notas")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Conteúdo
        content = tb.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        tb.Label(
            content,
            text="Como deseja exportar as notas?",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 8))

        # Frame com botões empilhados verticalmente
        buttons_frame = tb.Frame(content)
        buttons_frame.pack(fill=tk.X, pady=(6, 0))

        # Botão: Apenas Selecionadas
        btn_selected = tb.Button(
            buttons_frame,
            text="Exportar Notas Selecionadas",
            bootstyle=PRIMARY,  # PRIMARY para exportar selecionadas
            command=lambda: self._export_selected_confirm(selected_ids, dialog),
        )
        btn_selected.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_selected, "Exportar apenas as notas selecionadas para CSV.")

        # Botão: Todas as Notas
        btn_all = tb.Button(
            buttons_frame,
            text="Exportar Todas as Notas",
            bootstyle=INFO,  # INFO para exportar todas
            command=lambda: self._export_all_confirm(dialog),
        )
        btn_all.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_all, "Exportar todas as notas do sistema para CSV.")

        # Botão: Cancelar
        btn_cancel = tb.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
        )
        btn_cancel.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_cancel, "Cancelar a exportação de notas.")

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

    def _export_selected_confirm(self, selected_ids, dialog):
        """Exporta as notas selecionadas."""
        dialog.destroy()
        self.export_notes(selected_ids, "selecionadas")

    def _export_all_confirm(self, dialog):
        """Exporta todas as notas do sistema."""
        dialog.destroy()
        todas = self.database.get_all_notas()
        ids = [n[0] for n in todas]
        self.export_notes(ids, "todas")

    def export_notes(self, note_ids, tipo_exportacao):
        """
        Exporta para CSV uma lista de IDs de notas.
        Usa o file browser personalizado e pergunta se deseja abrir o arquivo.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"notas_{tipo_exportacao}_{timestamp}.csv"

        try:
            # Usa nosso FileBrowser personalizado (como em backup.py)
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
            # usuário cancelou
            return

        # Garantir extensão .csv
        if not file_path.lower().endswith(".csv"):
            file_path = f"{file_path}.csv"

        try:
            # Escrever CSV com encoding UTF-8 e delimitador correto
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                # Cabeçalho
                f.write("Data Emissao,Numero,Cliente,Valor,Telefone,Email,CNPJ,Endereco\n")

                # Linhas
                for note_id in note_ids:
                    nota = self.database.get_nota_por_id(note_id)
                    if not nota:
                        continue
                    
                    # Extrair dados da nota
                    data, numero, cliente, valor, telefone, email, cnpj, endereco = nota
                    
                    # CORREÇÃO: Formatar valor sem símbolo R$ e usando ponto como separador decimal
                    # para que o Excel reconheça como número
                    valor_float = float(valor) if isinstance(valor, (int, float)) else float(valor.replace(',', '.'))
                    valor_str = f"{valor_float:.2f}".replace('.', ',')  # Formato brasileiro: 2,00
                    
                    # Escrever linha formatada (sem aspas extras e valor numérico correto)
                    linha = f'{data},{numero},"{cliente}",{valor_str},"{telefone or ""}","{email or ""}","{cnpj or ""}","{endereco or ""}"\n'
                    f.write(linha)

            # Sucesso - mostrar informação
            show_info(
                self.parent, 
                f"Exportação concluída!\n\n"
                f"Arquivo salvo em:\n{file_path}\n\n"
                f"Total de notas exportadas: {len(note_ids)}"
            )

            # Perguntar se deseja abrir no editor de planilhas
            abrir = ask_yes_no(
                self.parent, 
                "Deseja abrir o arquivo no editor de planilhas padrão?"
            )
            if abrir == "Sim":
                self.abrir_arquivo_no_sistema(file_path)

        except Exception as e:
            tb_exc = traceback.format_exc()
            show_error(self.parent, f"Erro ao exportar arquivo: {str(e)}")

    def abrir_arquivo_no_sistema(self, file_path):
        """
        Abre o arquivo no aplicativo padrão do sistema.
        - Windows: os.startfile
        - macOS: open  
        - Linux: xdg-open (com fallback para gio)
        """
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(file_path)
            elif sistema == "Darwin":  # macOS
                subprocess.Popen(["open", file_path])
            else:
                # Linux/Unix
                try:
                    subprocess.Popen(["xdg-open", file_path])
                except Exception:
                    # Fallback para GNOME
                    try:
                        subprocess.Popen(["gio", "open", file_path])
                    except Exception as e:
                        show_warning(
                            self.parent, 
                            f"Não foi possível abrir automaticamente:\n{str(e)}"
                        )
        except Exception as e:
            show_warning(self.parent, f"Erro ao tentar abrir o arquivo:\n{str(e)}")