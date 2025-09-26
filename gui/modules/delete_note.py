# gui/modules/delete_note.py
"""
Interface para exclusão de notas fiscais usando ttkbootstrap.
Inclui tooltips e confirmações categorizadas.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..utils import (
    create_warning_tooltip,
    create_error_tooltip,
    create_info_tooltip,
    create_success_tooltip,
)
from ..utils.popups import ask_yes_no, show_info, show_error
from ..keys import EventKeys


class DeleteNotes(ttk.Frame):
    """Gerencia exclusão de notas fiscais."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

    def handle_delete(self, selected_ids):
        """Processa exclusão das notas com interface de escolha."""
        total_notas = self.database.get_total_notas()

        if total_notas == 0:
            # usa popup de erro/informação
            show_error(self.parent, "Nenhuma nota encontrada para exclusão!")
            return

        if selected_ids:
            self.show_delete_dialog(selected_ids)
        else:
            show_error(self.parent, "Nenhuma nota selecionada para exclusão!")

    def show_delete_dialog(self, selected_ids):
        """Exibe opções de exclusão: apenas selecionadas ou todas."""
        dialog = ttk.Toplevel(self.parent)
        dialog.title("Excluir Notas")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Conteúdo
        content = ttk.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            content,
            text="Como deseja excluir as notas?",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 8))

        # Frame com botões empilhados verticalmente (previnindo corte)
        buttons_frame = ttk.Frame(content)
        buttons_frame.pack(fill=tk.X, pady=(6, 0))

        # Botão: Apenas Selecionadas
        btn_selected = ttk.Button(
            buttons_frame,
            text="Apenas Selecionadas",
            bootstyle=WARNING,
            command=lambda: self._delete_selected_confirm(selected_ids, dialog),
        )
        btn_selected.pack(fill=tk.X, pady=6)
        create_warning_tooltip(btn_selected, "Excluir apenas as notas selecionadas.")

        # Botão: Todas as Notas -> antes pede confirmação de perigo
        btn_all = ttk.Button(
            buttons_frame,
            text="Todas as Notas",
            bootstyle=DANGER,
            command=lambda: self._confirm_and_delete_all(dialog),
        )
        btn_all.pack(fill=tk.X, pady=6)
        create_error_tooltip(
            btn_all, "Excluir todas as notas do sistema (irreversível)."
        )

        # Botão: Cancelar
        btn_cancel = ttk.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
        )
        btn_cancel.pack(fill=tk.X, pady=6)
        create_info_tooltip(btn_cancel, "Cancelar a exclusão de notas.")

        # Centralizar o diálogo com base no tamanho requisitado
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
        """Excluir selecionadas — destrói diálogo e executa exclusão."""
        try:
            for note_id in selected_ids:
                self.database.delete_nota(note_id)
        except Exception as e:
            show_error(self.parent, f"Erro ao excluir notas: {e}")
            dialog.destroy()
            return

        dialog.destroy()
        show_info(self.parent, f"{len(selected_ids)} nota(s) excluída(s) com sucesso!")

        # notifica controller para atualizar a view principal
        try:
            self.controller.refresh_main_menu()
        except Exception:
            try:
                self.controller.handle_event(EventKeys.REFRESH)
            except Exception:
                pass

    def _confirm_and_delete_all(self, dialog):
        """Mostra popup de perigo pedindo confirmação e deleta todas as notas se confirmado."""
        total = self.database.get_total_notas()
        msg = (
            "ATENÇÃO: Esta ação excluirá TODAS as "
            f"{total} nota(s) do sistema!\n\n"
            "Esta operação NÃO pode ser desfeita.\n\n"
            "Deseja realmente prosseguir?"
        )

        # ask_yes_no usa nosso CustomPopup com botões Sim (DANGER) / Não (SECONDARY)
        resposta = ask_yes_no(self.parent, msg, title="CONFIRMAÇÃO PERIGOSA")

        if resposta == "Sim":
            try:
                # apagar todas as notas numa única operação (corrigido)
                self.database.delete_all_notas()
            except Exception as e:
                dialog.destroy()
                show_error(self.parent, f"Erro ao excluir todas as notas: {e}")
                return

            dialog.destroy()
            show_info(
                self.parent, f"Todas as {total} nota(s) foram excluídas com sucesso!"
            )

            # notifica controller para atualizar a view principal
            try:
                self.controller.refresh_main_menu()
            except Exception:
                try:
                    self.controller.handle_event(EventKeys.REFRESH)
                except Exception:
                    pass
        else:
            # usuário escolheu "Não" — mantém o diálogo de exclusão principal aberto
            return
