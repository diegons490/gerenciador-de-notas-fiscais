# gui/utils/file_browser.py
"""
Explorador de arquivos personalizado usando ttkbootstrap.
Interface moderna inspirada no Dolphin do KDE Plasma 6.
"""

import os
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
from typing import List, Optional
from PIL import Image, ImageTk

# popups e tooltips local (mesmo pacote gui/utils)
from .popups import show_info, show_warning, show_error, ask_yes_no
from .tooltips import (
    create_info_tooltip,
    create_warning_tooltip,
    create_error_tooltip,
    create_success_tooltip,
)


class FileBrowser(tb.Toplevel):
    """
    Explorador de arquivos moderno com interface inspirada no Dolphin.
    """

    def __init__(
        self,
        parent,
        title="Explorador de Arquivos",
        initial_folder=None,
        file_types=None,
        select_folder=False,
        select_multiple=False,
        save_mode=False,
        default_filename="",
    ):
        super().__init__(parent)

        self.parent = parent
        self.title(title)
        self.geometry("900x600")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Configurações
        # CORREÇÃO: Se initial_folder for None ou vazio, usar diretório atual
        if initial_folder and os.path.isdir(initial_folder):
            self.current_path = initial_folder
        else:
            self.current_path = os.getcwd()

        self.file_types = file_types or [("Todos os arquivos", "*.*")]
        self.select_folder = select_folder
        self.select_multiple = select_multiple
        self.save_mode = save_mode
        self.default_filename = default_filename
        self.selected_files: List[str] = []

        # Histórico de navegação
        self.history: List[str] = []
        self.history_index = -1

        # Cache (placeholder se quiser adicionar ícones)
        self.icon_cache = {}

        self.create_widgets()
        self.load_directory(self.current_path)
        self.center_window()

        # Bindings úteis
        self.bind("<Escape>", lambda e: self.cancel_selection())
        self.bind("<F5>", lambda e: self.refresh_directory())

        # Esperar até que a janela seja fechada
        self.wait_window(self)

    # ---------------- UI ----------------
    def create_widgets(self):
        """Cria todos os widgets da interface."""
        main_frame = tb.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # toolbar, address, file list, status, filename (save_mode), actions
        self.create_toolbar(main_frame)
        self.create_address_bar(main_frame)
        self.create_file_list(main_frame)
        self.create_status_bar(main_frame)

        if self.save_mode:
            self.create_filename_input(main_frame)

        self.create_action_buttons(main_frame)

    def create_toolbar(self, parent):
        """Cria a barra de ferramentas superior."""
        toolbar = tb.Frame(parent)
        toolbar.pack(fill=X, pady=(0, 10))

        # navegação
        nav_frame = tb.Frame(toolbar)
        nav_frame.pack(side=LEFT)

        self.back_btn = tb.Button(
            nav_frame, text="◀", command=self.go_back, bootstyle=OUTLINE, width=3
        )
        self.back_btn.pack(side=LEFT, padx=(0, 2))
        create_info_tooltip(self.back_btn, "Voltar ao diretório anterior")

        self.forward_btn = tb.Button(
            nav_frame, text="▶", command=self.go_forward, bootstyle=OUTLINE, width=3
        )
        self.forward_btn.pack(side=LEFT, padx=(0, 2))
        create_info_tooltip(self.forward_btn, "Avançar no histórico")

        self.up_btn = tb.Button(
            nav_frame, text="↑", command=self.go_up, bootstyle=OUTLINE, width=3
        )
        self.up_btn.pack(side=LEFT, padx=(0, 10))
        create_info_tooltip(self.up_btn, "Ir para a pasta pai")

        # ações
        action_frame = tb.Frame(toolbar)
        action_frame.pack(side=LEFT)

        self.home_btn = tb.Button(
            action_frame, text="🏠", command=self.go_home, bootstyle=OUTLINE, width=3
        )
        self.home_btn.pack(side=LEFT, padx=(0, 2))
        create_info_tooltip(self.home_btn, "Ir para a pasta Home")

        self.refresh_btn = tb.Button(
            action_frame,
            text="↻",
            command=self.refresh_directory,
            bootstyle=OUTLINE,
            width=3,
        )
        self.refresh_btn.pack(side=LEFT, padx=(0, 2))
        create_info_tooltip(self.refresh_btn, "Recarregar diretório (F5)")

        self.new_folder_btn = tb.Button(
            action_frame,
            text="📁",
            command=self.create_new_folder,
            bootstyle=OUTLINE,
            width=3,
        )
        self.new_folder_btn.pack(side=LEFT, padx=(0, 10))
        create_info_tooltip(self.new_folder_btn, "Criar nova pasta")

        # pesquisa
        search_frame = tb.Frame(toolbar)
        search_frame.pack(side=RIGHT, fill=X, expand=True)

        tb.Label(search_frame, text="Pesquisar:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tb.Entry(
            search_frame, textvariable=self.search_var, width=20
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        create_info_tooltip(
            self.search_entry, "Digite para buscar nome de arquivo/pasta"
        )

    def create_address_bar(self, parent):
        """Cria a barra de endereço."""
        address_frame = tb.Frame(parent)
        address_frame.pack(fill=X, pady=(0, 10))

        tb.Label(address_frame, text="Localização:").pack(side=LEFT, padx=(0, 5))
        self.address_var = tk.StringVar()
        self.address_entry = tb.Entry(address_frame, textvariable=self.address_var)
        self.address_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.address_entry.bind("<Return>", self.on_address_changed)
        create_info_tooltip(self.address_entry, "Digite um caminho e pressione Enter")

        tb.Button(
            address_frame, text="Ir", command=self.on_address_changed, bootstyle=OUTLINE
        ).pack(side=LEFT)
        create_info_tooltip(address_frame, "Ir para o caminho digitado")

    def create_file_list(self, parent):
        """Cria a lista de arquivos com Treeview."""
        list_frame = tb.Frame(parent)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # header simples (visualmente)
        header_frame = tb.Frame(list_frame)
        header_frame.pack(fill=X)
        tb.Label(header_frame, text="Nome", font=("Helvetica", 10, "bold")).pack(
            side=LEFT, padx=(8, 220)
        )
        tb.Label(header_frame, text="Tamanho", font=("Helvetica", 10, "bold")).pack(
            side=LEFT, padx=(0, 90)
        )
        tb.Label(header_frame, text="Modificado", font=("Helvetica", 10, "bold")).pack(
            side=LEFT
        )
        # treeview
        columns = ("name", "size", "modified")
        self.treeview = tb.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode=EXTENDED if self.select_multiple else BROWSE,
            height=15,
        )

        self.treeview.column("#0", width=0, stretch=False)
        self.treeview.column("name", width=400, minwidth=200)
        self.treeview.column("size", width=100, minwidth=80)
        self.treeview.column("modified", width=150, minwidth=120)

        self.treeview.heading("name", text="Nome")
        self.treeview.heading("size", text="Tamanho")
        self.treeview.heading("modified", text="Modificado")

        scrollbar = tb.Scrollbar(
            list_frame, orient=VERTICAL, command=self.treeview.yview
        )
        self.treeview.configure(yscrollcommand=scrollbar.set)

        self.treeview.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.treeview.bind("<Double-1>", self.on_item_double_click)
        self.treeview.bind("<<TreeviewSelect>>", self.on_selection_changed)
        create_info_tooltip(
            self.treeview, "Lista de arquivos e pastas; duplo clique para abrir"
        )

    def create_status_bar(self, parent):
        """Cria a barra de status inferior."""
        self.status_frame = tb.Frame(parent)
        self.status_frame.pack(fill=X, pady=(0, 10))
        self.status_label = tb.Label(self.status_frame, text="Pronto")
        self.status_label.pack(side=LEFT)

    def create_filename_input(self, parent):
        """Cria a entrada para nome do arquivo (modo salvar)."""
        filename_frame = tb.Frame(parent)
        filename_frame.pack(fill=X, pady=(0, 10))
        tb.Label(filename_frame, text="Nome do arquivo:").pack(side=LEFT, padx=(0, 5))
        self.filename_var = tk.StringVar(value=self.default_filename)
        self.filename_entry = tb.Entry(filename_frame, textvariable=self.filename_var)
        self.filename_entry.pack(side=LEFT, fill=X, expand=True)
        create_info_tooltip(self.filename_entry, "Nome do arquivo a salvar")

        # CORREÇÃO: Adicionar evento para atualizar o botão quando o texto mudar
        def on_filename_change(*args):
            if self.save_mode and hasattr(self, "select_btn"):
                if self.filename_var.get().strip():
                    self.select_btn.config(state=NORMAL)
                else:
                    self.select_btn.config(state=DISABLED)

        self.filename_var.trace_add("write", on_filename_change)

        # CORREÇÃO: Atualizar estado do botão após criar o campo
        if self.save_mode and hasattr(self, "select_btn"):
            if self.filename_var.get().strip():
                self.select_btn.config(state=NORMAL)

    def create_action_buttons(self, parent):
        """Cria os botões de ação."""
        button_frame = tb.Frame(parent)
        button_frame.pack(fill=X)

        tb.Button(
            button_frame,
            text="Cancelar",
            command=self.cancel_selection,
            bootstyle=SECONDARY,
            width=10,
        ).pack(side=RIGHT, padx=(5, 0))
        create_info_tooltip(button_frame, "Cancelar e fechar o explorador")

        select_text = (
            "Selecionar Pasta"
            if self.select_folder
            else "Salvar" if self.save_mode else "Selecionar"
        )
        self.select_btn = tb.Button(
            button_frame,
            text=select_text,
            command=self.confirm_selection,
            bootstyle=PRIMARY,
            width=10,
        )
        self.select_btn.pack(side=RIGHT)

        # CORREÇÃO: Não desabilitar o botão inicialmente no modo save_mode
        # Em vez disso, verificar o estado inicial após criar todos os widgets
        if self.save_mode:
            # No modo salvar, habilitar se já houver um filename
            if hasattr(self, "filename_var") and self.filename_var.get():
                self.select_btn.config(state=NORMAL)
            else:
                self.select_btn.config(state=DISABLED)
        elif self.select_folder:
            # No modo selecionar pasta, sempre habilitado
            self.select_btn.config(state=NORMAL)
        else:
            # No modo abrir, desabilitado inicialmente
            self.select_btn.config(state=DISABLED)

        create_info_tooltip(self.select_btn, "Confirmar seleção")

    # ---------------- Directory operations ----------------
    def load_directory(self, path: str):
        """Carrega o conteúdo do diretório especificado."""
        try:
            if not os.path.exists(path) or not os.path.isdir(path):
                show_error(self, f"Diretório não encontrado: {path}")
                return

            # atualizar histórico de navegação
            if not self.history or self.history[self.history_index] != path:
                self.history = self.history[: self.history_index + 1]
                self.history.append(path)
                self.history_index = len(self.history) - 1

            self.current_path = path
            self.address_var.set(path)

            # limpar treeview
            for item in self.treeview.get_children():
                self.treeview.delete(item)

            items = os.listdir(path)
            folders = []
            files = []

            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    folders.append((item, full_path))
                else:
                    if self.filter_file(item):
                        files.append((item, full_path))

            folders.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())

            if path != os.path.dirname(path):
                self.treeview.insert("", "end", iid="..", values=("..", "Pasta", ""))

            for name, full_path in folders:
                size = self.get_folder_size(full_path)
                modified = self.get_file_modified(full_path)
                self.treeview.insert(
                    "", "end", iid=full_path, values=(name, size, modified)
                )

            for name, full_path in files:
                size = self.get_file_size(full_path)
                modified = self.get_file_modified(full_path)
                self.treeview.insert(
                    "", "end", iid=full_path, values=(name, size, modified)
                )

            total_items = len(folders) + len(files)
            self.status_label.config(text=f"{total_items} itens")
            self.update_navigation_buttons()

        except PermissionError:
            show_error(self, f"Sem permissão para acessar: {path}")
        except Exception as e:
            show_error(self, f"Erro ao carregar diretório: {str(e)}")

    def filter_file(self, filename: str) -> bool:
        """Filtra arquivos baseado nos tipos especificados."""
        if not self.file_types or any(ft[1] == "*.*" for ft in self.file_types):
            return True

        ext = os.path.splitext(filename)[1].lower()
        for desc, pattern in self.file_types:
            if pattern == "*.*":
                return True
            patterns = pattern.lower().split(";")
            for p in patterns:
                p = p.strip()
                if p == "*":
                    return True
                if p.startswith("*."):
                    pattern_ext = p[2:]
                    if ext == pattern_ext or (pattern_ext and ext == "." + pattern_ext):
                        return True
                if p.startswith(".") and ext == p:
                    return True
                if not p.startswith(".") and not p.startswith("*") and ext == "." + p:
                    return True
        return False

    def get_file_size(self, filepath: str) -> str:
        """Retorna o tamanho do arquivo formatado."""
        try:
            size = os.path.getsize(filepath)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        except:
            return "?"

    def get_folder_size(self, folderpath: str) -> str:
        """Retorna o tamanho aproximado da pasta (placeholder)."""
        return "Pasta"

    def get_file_modified(self, filepath: str) -> str:
        """Retorna a data de modificação formatada."""
        try:
            mtime = os.path.getmtime(filepath)
            return datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        except:
            return "?"

    # ---------------- Events ----------------
    def on_item_double_click(self, event=None):
        """Manipula duplo clique em itens."""
        item = self.treeview.selection()
        if item:
            item_id = item[0]
            if item_id == "..":
                self.go_up()
            elif os.path.isdir(item_id):
                self.load_directory(item_id)

    def on_selection_changed(self, event=None):
        """Manipula mudança na seleção."""
        selected = self.treeview.selection()
        self.selected_files = []

        for item_id in selected:
            if item_id != ".." and not os.path.isdir(item_id):
                self.selected_files.append(item_id)

        # atualizar campo filename no modo salvar
        if self.save_mode and hasattr(self, "filename_var") and self.selected_files:
            filename = os.path.basename(self.selected_files[0])
            self.filename_var.set(filename)

        # CORREÇÃO: Lógica melhorada para habilitar/desabilitar botão
        if self.select_folder:
            # Modo selecionar pasta: sempre habilitado
            self.select_btn.config(state=NORMAL)
        elif self.save_mode:
            # Modo salvar: habilitar se houver nome de arquivo
            if hasattr(self, "filename_var") and self.filename_var.get().strip():
                self.select_btn.config(state=NORMAL)
            else:
                self.select_btn.config(state=DISABLED)
        else:
            # Modo abrir: habilitar se houver arquivos selecionados
            self.select_btn.config(state=NORMAL if self.selected_files else DISABLED)

    def on_address_changed(self, event=None):
        """Manipula mudança no endereço."""
        new_path = self.address_var.get()
        if os.path.isdir(new_path):
            self.load_directory(new_path)
        else:
            show_error(self, "Diretório não encontrado")
            self.address_var.set(self.current_path)

    def on_search(self, event=None):
        """Pesquisa simples (destaca itens que contém o termo)."""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.load_directory(self.current_path)
            return

        # simples: desmarcar tudo e destacar correspondências
        for item in self.treeview.get_children():
            values = self.treeview.item(item, "values")
            if values and search_term in str(values[0]).lower():
                try:
                    self.treeview.reattach(item, "", "end")
                except Exception:
                    pass
                self.treeview.selection_set(item)
                self.treeview.see(item)
            else:
                try:
                    self.treeview.detach(item)
                except Exception:
                    pass

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.load_directory(self.history[self.history_index])

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.load_directory(self.history[self.history_index])

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.load_directory(parent)

    def go_home(self):
        home_path = os.path.expanduser("~")
        self.load_directory(home_path)

    def refresh_directory(self):
        self.load_directory(self.current_path)

    # ---------------- new-folder (corrigida) ----------------
    # ---------------- new-folder (ajustada para sempre "Nova Pasta") ----------------
    def create_new_folder(self):
        """
        Cria uma nova pasta. Pergunta o nome ao usuário em um dialog simples,
        usa os popups para informar sucesso/erro e atualiza a listagem.
        O campo virá sempre preenchido com 'Nova Pasta' (editável).
        """
        # Sempre usar "Nova Pasta" como valor inicial, conforme pedido
        folder_name = self._prompt_for_new_folder_name(default="Nova Pasta")
        if folder_name is None:
            return  # usuário cancelou

        folder_name = folder_name.strip()
        if not folder_name:
            show_error(self, "Nome de pasta inválido.")
            return

        new_path = os.path.join(self.current_path, folder_name)
        try:
            os.makedirs(new_path, exist_ok=False)
            show_info(self, f"Pasta '{folder_name}' criada com sucesso!")
            self.refresh_directory()
        except FileExistsError:
            show_error(self, f"A pasta '{folder_name}' já existe!")
        except PermissionError:
            show_error(self, f"Sem permissão para criar a pasta: {new_path}")
        except Exception as e:
            show_error(self, f"Erro ao criar pasta: {str(e)}")

    def _prompt_for_new_folder_name(self, default="Nova Pasta") -> Optional[str]:
        """Abre um pequeno diálogo modal pedindo o nome da nova pasta.
        O campo vem preenchido com `default`. Retorna string ou None.
        """
        dlg = tb.Toplevel(self)
        dlg.title("Criar Pasta")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=12)
        frm.pack(fill=BOTH, expand=True)

        tb.Label(frm, text="Nome da nova pasta:", font=("Helvetica", 11)).pack(
            anchor="w", pady=(0, 6)
        )
        name_var = tk.StringVar(value=default)
        entry = tb.Entry(frm, textvariable=name_var)
        entry.pack(fill=X, pady=(0, 8))
        entry.focus_set()

        # Seleciona todo o texto para permitir sobrescrever imediatamente
        try:
            entry.selection_range(0, tk.END)
        except Exception:
            pass

        btn_frame = tb.Frame(frm)
        btn_frame.pack(fill=X, pady=(6, 0))

        result = {"value": None}

        def on_ok():
            result["value"] = name_var.get()
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        tb.Button(btn_frame, text="Criar", bootstyle=SUCCESS, command=on_ok).pack(
            side=LEFT, padx=6, fill=X, expand=True
        )
        tb.Button(
            btn_frame, text="Cancelar", bootstyle=SECONDARY, command=on_cancel
        ).pack(side=LEFT, padx=6, fill=X, expand=True)

        # centralizar o diálogo usando tamanho requisitado
        dlg.update_idletasks()
        w = dlg.winfo_reqwidth()
        h = dlg.winfo_reqheight()
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        dlg.wait_window()
        return result["value"]

    # ---------------- selection ----------------
    def has_valid_filename(self):
        """Verifica se há um nome de arquivo válido no modo salvar."""
        if not self.save_mode or not hasattr(self, "filename_var"):
            return False
        return bool(self.filename_var.get().strip())

    # CORREÇÃO: Atualizar o método confirm_selection
    def confirm_selection(self):
        """Confirma a seleção e fecha o diálogo."""
        if self.select_folder:
            self.selected_files = [self.current_path]
        elif self.save_mode:
            filename = getattr(self, "filename_var", tk.StringVar()).get().strip()
            if filename:
                file_path = os.path.join(self.current_path, filename)
                self.selected_files = [file_path]
            else:
                show_error(self, "Digite um nome de arquivo válido!")
                return
        else:
            # em modo abrir
            if self.selected_files:
                pass
            else:
                show_error(self, "Nenhum arquivo selecionado!")
                return

        if self.selected_files:
            self.destroy()
        else:
            show_error(self, "Nenhum arquivo selecionado")

    def cancel_selection(self):
        self.selected_files = []
        self.destroy()

    def update_navigation_buttons(self):
        """Atualiza o estado dos botões de navegação."""
        self.back_btn.config(state=NORMAL if self.history_index > 0 else DISABLED)
        self.forward_btn.config(
            state=NORMAL if self.history_index < len(self.history) - 1 else DISABLED
        )
        self.up_btn.config(
            state=(
                NORMAL
                if self.current_path != os.path.dirname(self.current_path)
                else DISABLED
            )
        )

    # ---------------- window utils ----------------
    def center_window(self):
        """Centraliza a janela na tela (usa requisitado como fallback)."""
        self.update_idletasks()
        try:
            width = self.winfo_width() or self.winfo_reqwidth()
            height = self.winfo_height() or self.winfo_reqheight()
        except tk.TclError:
            width, height = 900, 600

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        if width <= 1:
            width = min(900, screen_w - 80)
        if height <= 1:
            height = min(600, screen_h - 80)

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


# -------- helper functions for API compatibility (like filedialog) --------
def askopenfilename(
    parent, title="Abrir arquivo", initialfile="", filetypes=None, select_multiple=False
):
    # CORREÇÃO: Se initialfile for apenas nome de arquivo, usar diretório atual
    if initialfile and os.path.isdir(
        os.path.dirname(initialfile) if os.path.dirname(initialfile) else False
    ):
        initial_folder = os.path.dirname(initialfile)
    else:
        initial_folder = os.getcwd()

    browser = FileBrowser(
        parent=parent,
        title=title,
        initial_folder=initial_folder,
        file_types=filetypes,
        select_multiple=select_multiple,
        save_mode=False,
    )
    if select_multiple:
        return browser.selected_files
    else:
        return browser.selected_files[0] if browser.selected_files else ""


def asksaveasfilename(parent, title="Salvar como", initialfile="", filetypes=None):
    # CORREÇÃO: Se initialfile for apenas nome de arquivo, usar diretório atual
    initial_folder = (
        os.path.dirname(initialfile)
        if initialfile and os.path.dirname(initialfile)
        else os.getcwd()
    )

    browser = FileBrowser(
        parent=parent,
        title=title,
        initial_folder=initial_folder,
        file_types=filetypes,
        save_mode=True,
        default_filename=os.path.basename(initialfile) if initialfile else "",
    )
    return browser.selected_files[0] if browser.selected_files else ""
