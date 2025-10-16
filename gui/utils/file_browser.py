# gui/utils/file_browser/file_browser.py
"""
Explorador de arquivos personalizado usando ttkbootstrap.
Interface moderna inspirada no Dolphin do KDE Plasma 6.
"""

import os
import sys
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
from typing import List, Optional, Tuple
from PIL import Image, ImageTk

# Adiciona o diretório raiz do projeto ao path para importações absolutas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importações absolutas dos módulos utilitários
try:
    from gui.utils.popups import show_info, show_warning, show_error, ask_yes_no
    from gui.utils.tooltips import (
        create_info_tooltip,
        create_warning_tooltip,
        create_error_tooltip,
        create_success_tooltip,
    )
except ImportError as e:
    print(f"Erro ao importar módulos utilitários: {e}")
    # Fallback básico se as importações falharem
    def show_info(parent, message):
        tk.messagebox.showinfo("Informação", message)
    
    def show_warning(parent, message):
        tk.messagebox.showwarning("Aviso", message)
    
    def show_error(parent, message):
        tk.messagebox.showerror("Erro", message)
    
    def ask_yes_no(parent, question):
        return tk.messagebox.askyesno("Confirmação", question)
    
    def create_info_tooltip(widget, text):
        pass
    
    def create_warning_tooltip(widget, text):
        pass
    
    def create_error_tooltip(widget, text):
        pass
    
    def create_success_tooltip(widget, text):
        pass


class FileBrowserConfig:
    """Classe para gerenciar configurações do FileBrowser usando caminhos relativos"""
    
    def __init__(self):
        self.config_file = self.get_config_path()
        self.ensure_config_dir()
    
    def get_config_path(self):
        """Retorna o caminho do arquivo de configuração dentro da pasta file_browser"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # CORREÇÃO: Agora salva dentro da pasta file_browser
        file_browser_dir = os.path.join(current_dir, "file_browser")
        config_file = os.path.join(file_browser_dir, "file_browser_config.json")
        return config_file
    
    def ensure_config_dir(self):
        """Garante que o diretório do arquivo de configuração existe"""
        try:
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            print(f"Erro ao criar diretório de configuração: {e}")
    
    def save_last_path(self, path):
        """Salva o último caminho acessado"""
        try:
            # Verifica se o caminho é acessível sem privilégios de admin
            if self.is_path_accessible(path):
                config_data = self.load_config()
                config_data["last_path"] = path
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def load_last_path(self):
        """Carrega o último caminho salvo"""
        try:
            config_data = self.load_config()
            last_path = config_data.get("last_path", "")
            if last_path and self.is_path_accessible(last_path):
                return last_path
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
        return None
    
    def is_path_accessible(self, path):
        """Verifica se o caminho é acessível sem privilégios de administrador"""
        try:
            if not path or not os.path.exists(path):
                return False
            
            # No Windows, verifica se é um caminho do sistema que requer admin
            if os.name == 'nt':
                system_paths = [
                    os.environ.get('SYSTEMROOT', 'C:\\Windows'),
                    os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                    os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
                ]
                
                path_lower = path.lower()
                for system_path in system_paths:
                    if system_path and path_lower.startswith(system_path.lower()):
                        # Verifica se temos permissão de escrita
                        test_file = os.path.join(path, 'write_test.tmp')
                        try:
                            with open(test_file, 'w') as f:
                                f.write('test')
                            os.remove(test_file)
                            return True
                        except (IOError, OSError, PermissionError):
                            return False
                
                # Para caminhos não-sistema, verifica permissão básica
                test_dir = os.path.join(path, 'test_access')
                try:
                    os.makedirs(test_dir, exist_ok=True)
                    os.rmdir(test_dir)
                    return True
                except (IOError, OSError, PermissionError):
                    return False
            else:
                # Em sistemas Unix, verifica permissão básica
                return os.access(path, os.R_OK | os.W_OK)
                
        except Exception:
            return False
    
    def load_config(self):
        """Carrega todo o arquivo de configuração"""
        default_config = {
            "last_path": "",
            "window_width": 1000,
            "window_height": 700
        }
        
        if not os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao criar arquivo de configuração: {e}")
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar arquivo de configuração: {e}")
            return default_config
    
    def save_window_size(self, width, height):
        """Salva o tamanho da janela"""
        try:
            config_data = self.load_config()
            config_data["window_width"] = width
            config_data["window_height"] = height
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar tamanho da janela: {e}")
    
    def load_window_size(self):
        """Carrega o tamanho da janela salvo"""
        try:
            config_data = self.load_config()
            width = config_data.get("window_width", 1000)
            height = config_data.get("window_height", 700)
            return width, height
        except Exception as e:
            print(f"Erro ao carregar tamanho da janela: {e}")
            return 1000, 700


class IconManager:
    """Gerenciador de ícones PNG para o FileBrowser usando caminhos relativos"""
    
    def __init__(self):
        self.icons_dir = self.get_icons_dir()
        self.icon_cache = {}
        self.photo_references = []  # Lista para manter referências às PhotoImages
        self.emoji_fallbacks = {
            'back': '⏪',
            'forward': '⏩', 
            'up': '⏫',
            'home': '🏠',
            'reload': '🔄',
            'new-folder': '📁+',
            'search': '🔍',
            'cancel': '❌',
            'select': '✅',
            'save': '💾',
            'file': '📄',
            'folder': '📁',
            'graph': '📊',
            'time': '⏰'
        }
    
    def get_icons_dir(self):
        """Retorna o diretório de ícones usando caminho relativo"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Os ícones estão em file_browser/file_browser_icons dentro do diretório atual
        icons_dir = os.path.join(current_dir, "file_browser", "file_browser_icons")
        return icons_dir
    
    def load_icon(self, icon_name, size=(24, 24)):
        """Carrega um ícone PNG do diretório de ícones"""
        try:
            icon_path = os.path.join(self.icons_dir, f"{icon_name}.png")
            
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                # Converter para modo RGBA se necessário para transparência
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                image = image.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Mantém referência para evitar garbage collection
                self.photo_references.append(photo)
                return photo
        except Exception as e:
            print(f"Erro ao carregar ícone {icon_name}: {e}")
        
        # Fallback para emoji se o PNG não for encontrado
        return self.emoji_fallbacks.get(icon_name, '❓')
    
    def get_icon(self, icon_name, size=(24, 24)):
        """Obtém um ícone do cache ou carrega se necessário"""
        cache_key = f"{icon_name}_{size[0]}x{size[1]}"
        if cache_key not in self.icon_cache:
            self.icon_cache[cache_key] = self.load_icon(icon_name, size)
        return self.icon_cache[cache_key]
    
    def is_image_icon(self, icon):
        """Verifica se o ícone é uma imagem (não texto/emoji)"""
        return hasattr(icon, '_PhotoImage__photo') or hasattr(icon, 'photo') or isinstance(icon, tk.PhotoImage)


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
        
        # Carregar configurações
        self.config = FileBrowserConfig()
        self.icon_manager = IconManager()
        self.icon_references = {}

        # Configurar tamanho da janela
        width, height = self.config.load_window_size()
        self.geometry(f"{width}x{height}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Configurar caminho atual - prioriza caminhos acessíveis
        self.current_path = self.get_accessible_initial_path(initial_folder)

        self.file_types = file_types or [("Todos os arquivos", "*.*")]
        self.select_folder = select_folder
        self.select_multiple = select_multiple
        self.save_mode = save_mode
        self.default_filename = default_filename
        self.selected_files: List[str] = []

        self.history: List[str] = []
        self.history_index = -1

        self.create_widgets()
        self.load_directory(self.current_path)
        self.center_window()

        # Bind events
        self.bind("<Escape>", lambda e: self.cancel_selection())
        self.bind("<F5>", lambda e: self.refresh_directory())
        self.bind("<Configure>", self.on_window_resize)
        self.bind("<Destroy>", lambda e: self.on_destroy())

        self.wait_window(self)

    def get_accessible_initial_path(self, initial_folder=None):
        """Obtém um caminho inicial acessível sem privilégios de admin"""
        possible_paths = []
        
        # 1. Primeiro tenta o caminho fornecido
        if initial_folder and os.path.isdir(initial_folder):
            possible_paths.append(initial_folder)
        
        # 2. Tenta o último caminho salvo
        last_path = self.config.load_last_path()
        if last_path and os.path.isdir(last_path):
            possible_paths.append(last_path)
        
        # 3. Diretórios do usuário que são sempre acessíveis
        user_dirs = self.get_user_accessible_directories()
        
        # Adiciona diretórios do usuário que existem
        for user_dir in user_dirs:
            if os.path.isdir(user_dir):
                possible_paths.append(user_dir)
        
        # 4. Diretório atual do script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(current_dir):
            possible_paths.append(current_dir)
        
        # 5. Diretório de trabalho atual
        working_dir = os.getcwd()
        if os.path.isdir(working_dir):
            possible_paths.append(working_dir)
        
        # Encontra o primeiro caminho acessível
        for path in possible_paths:
            if self.config.is_path_accessible(path):
                return path
        
        # Fallback: diretório home do usuário
        return os.path.expanduser("~")

    def get_user_accessible_directories(self):
        """Retorna lista de diretórios do usuário acessíveis, evitando duplicatas virtuais"""
        user_home = os.path.expanduser("~")
        accessible_dirs = [user_home]
        
        # Diretórios comuns do usuário
        common_dirs = [
            "Documents", "Documentos",  # Inglês e Português
            "Desktop", "Área de Trabalho",
            "Downloads", "Transferências",
            "Pictures", "Imagens",
            "Music", "Música",
            "Videos", "Vídeos"
        ]
        
        for dir_name in common_dirs:
            dir_path = os.path.join(user_home, dir_name)
            if os.path.isdir(dir_path):
                accessible_dirs.append(dir_path)
        
        # Remove duplicatas virtuais do Windows
        return self.filter_virtual_folders(accessible_dirs)

    def filter_virtual_folders(self, dir_list):
        """Filtra pastas virtuais e links simbólicos duplicados no Windows"""
        if os.name != 'nt':
            return dir_list
        
        filtered_dirs = []
        real_paths = set()
        
        for dir_path in dir_list:
            try:
                # Obtém o caminho real (resolve links simbólicos)
                real_path = os.path.realpath(dir_path)
                
                # Verifica se é uma pasta virtual comum do Windows
                dir_name = os.path.basename(real_path).lower()
                virtual_names = {
                    'meus documentos', 'my documents', 'documents', 'documentos',
                    'minhas imagens', 'my pictures', 'pictures', 'imagens',
                    'minha música', 'my music', 'music', 'música',
                    'meus vídeos', 'my videos', 'videos', 'vídeos'
                }
                
                # Se não for um caminho duplicado e não for uma pasta virtual problemática
                if (real_path not in real_paths and 
                    not any(virtual_name in dir_name for virtual_name in virtual_names)):
                    real_paths.add(real_path)
                    filtered_dirs.append(dir_path)
                    
            except (OSError, ValueError):
                # Se houver erro ao obter o caminho real, inclui de qualquer maneira
                filtered_dirs.append(dir_path)
        
        return filtered_dirs

    def on_window_resize(self, event):
        """Salva o tamanho da janela quando redimensionada"""
        if event.widget == self and (event.width > 100 and event.height > 100):
            self.config.save_window_size(event.width, event.height)

    def on_destroy(self):
        """Salva configurações quando a janela é fechada"""
        try:
            if hasattr(self, 'current_path') and self.config.is_path_accessible(self.current_path):
                self.config.save_last_path(self.current_path)
        except Exception as e:
            print(f"Erro ao salvar último caminho: {e}")

    def create_widgets(self):
        """Cria todos os widgets da interface"""
        main_frame = tb.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=12, pady=12)

        self.create_toolbar(main_frame)
        self.create_address_bar(main_frame)
        self.create_file_list(main_frame)
        self.create_status_bar(main_frame)

        if self.save_mode:
            self.create_filename_input(main_frame)

        self.create_action_buttons(main_frame)

    def create_toolbar(self, parent):
        """Cria a barra de ferramentas com botões de navegação"""
        toolbar = tb.Frame(parent)
        toolbar.pack(fill=X, pady=(0, 12))

        nav_frame = tb.Frame(toolbar)
        nav_frame.pack(side=LEFT)

        # Botão Voltar
        back_icon = self.icon_manager.get_icon('back', size=(28, 28))
        self.back_btn = tb.Button(
            nav_frame,
            command=self.go_back,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(back_icon):
            self.back_btn.configure(image=back_icon)
        else:
            self.back_btn.configure(text=str(back_icon))
        self.back_btn.pack(side=LEFT, padx=(0, 3))
        create_info_tooltip(self.back_btn, "Voltar ao diretório anterior")

        # Botão Forward
        forward_icon = self.icon_manager.get_icon('forward', size=(28, 28))
        self.forward_btn = tb.Button(
            nav_frame,
            command=self.go_forward,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(forward_icon):
            self.forward_btn.configure(image=forward_icon)
        else:
            self.forward_btn.configure(text=str(forward_icon))
        self.forward_btn.pack(side=LEFT, padx=(0, 3))
        create_info_tooltip(self.forward_btn, "Avançar no histórico")

        # Botão Up
        up_icon = self.icon_manager.get_icon('up', size=(28, 28))
        self.up_btn = tb.Button(
            nav_frame,
            command=self.go_up,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(up_icon):
            self.up_btn.configure(image=up_icon)
        else:
            self.up_btn.configure(text=str(up_icon))
        self.up_btn.pack(side=LEFT, padx=(0, 15))
        create_info_tooltip(self.up_btn, "Ir para a pasta pai")

        action_frame = tb.Frame(toolbar)
        action_frame.pack(side=LEFT)

        # Botão Home
        home_icon = self.icon_manager.get_icon('home', size=(28, 28))
        self.home_btn = tb.Button(
            action_frame,
            command=self.go_home,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(home_icon):
            self.home_btn.configure(image=home_icon)
        else:
            self.home_btn.configure(text=str(home_icon))
        self.home_btn.pack(side=LEFT, padx=(0, 3))
        create_info_tooltip(self.home_btn, "Ir para a pasta Home")

        # Botão Recarregar
        reload_icon = self.icon_manager.get_icon('reload', size=(28, 28))
        self.refresh_btn = tb.Button(
            action_frame,
            command=self.refresh_directory,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(reload_icon):
            self.refresh_btn.configure(image=reload_icon)
        else:
            self.refresh_btn.configure(text=str(reload_icon))
        self.refresh_btn.pack(side=LEFT, padx=(0, 3))
        create_info_tooltip(self.refresh_btn, "Recarregar diretório (F5)")

        # Botão Nova Pasta
        new_folder_icon = self.icon_manager.get_icon('new-folder', size=(28, 28))
        self.new_folder_btn = tb.Button(
            action_frame,
            command=self.create_new_folder,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(new_folder_icon):
            self.new_folder_btn.configure(image=new_folder_icon)
        else:
            self.new_folder_btn.configure(text=str(new_folder_icon))
        self.new_folder_btn.pack(side=LEFT, padx=(0, 15))
        create_info_tooltip(self.new_folder_btn, "Criar nova pasta")

        search_frame = tb.Frame(toolbar)
        search_frame.pack(side=RIGHT, fill=X, expand=True)

        # Ícone de pesquisa
        search_icon = self.icon_manager.get_icon('search', size=(24, 24))
        if self.icon_manager.is_image_icon(search_icon):
            self.search_label = tb.Label(search_frame, image=search_icon)
        else:
            self.search_label = tb.Label(search_frame, text=str(search_icon))
        self.search_label.pack(side=LEFT, padx=(0, 8))
        create_info_tooltip(self.search_label, "Pesquisar")

        self.search_var = tk.StringVar()
        self.search_entry = tb.Entry(
            search_frame, textvariable=self.search_var, width=25
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        create_info_tooltip(
            self.search_entry, "Digite para buscar nome de arquivo/pasta"
        )

    def create_address_bar(self, parent):
        """Cria a barra de endereço"""
        address_frame = tb.Frame(parent)
        address_frame.pack(fill=X, pady=(0, 12))

        tb.Label(address_frame, text="Localização:").pack(side=LEFT, padx=(0, 8))
        self.address_var = tk.StringVar()
        self.address_entry = tb.Entry(address_frame, textvariable=self.address_var)
        self.address_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        self.address_entry.bind("<Return>", self.on_address_changed)
        create_info_tooltip(self.address_entry, "Digite um caminho e pressione Enter")

        go_icon = self.icon_manager.get_icon('select', size=(20, 20))
        self.go_btn = tb.Button(
            address_frame,
            command=self.on_address_changed,
            bootstyle=OUTLINE,
            width=6
        )
        if self.icon_manager.is_image_icon(go_icon):
            self.go_btn.configure(image=go_icon)
        else:
            self.go_btn.configure(text=str(go_icon))
        self.go_btn.pack(side=LEFT)
        create_info_tooltip(self.go_btn, "Ir para o caminho digitado")

    def create_file_list(self, parent):
        """Cria a lista de arquivos"""
        list_frame = tb.Frame(parent)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 12))

        columns = ("name", "size", "modified")
        self.treeview = tb.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode=EXTENDED if self.select_multiple else BROWSE,
            height=18,
        )

        self.treeview.column("#0", width=0, stretch=False)
        self.treeview.column("name", width=450, minwidth=250)
        self.treeview.column("size", width=120, minwidth=90)
        self.treeview.column("modified", width=180, minwidth=140)

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
        """Cria a barra de status"""
        self.status_frame = tb.Frame(parent)
        self.status_frame.pack(fill=X, pady=(0, 12))

        info_icon = self.icon_manager.get_icon('graph', size=(20, 20))
        if self.icon_manager.is_image_icon(info_icon):
            self.status_icon_label = tb.Label(self.status_frame, image=info_icon)
        else:
            self.status_icon_label = tb.Label(self.status_frame, text=str(info_icon))
        self.status_icon_label.pack(side=LEFT, padx=(0, 8))

        self.status_label = tb.Label(self.status_frame, text="Pronto")
        self.status_label.pack(side=LEFT)

    def create_filename_input(self, parent):
        """Cria o campo de entrada de nome de arquivo (modo salvar)"""
        filename_frame = tb.Frame(parent)
        filename_frame.pack(fill=X, pady=(0, 12))

        file_icon = self.icon_manager.get_icon('file', size=(20, 20))
        if self.icon_manager.is_image_icon(file_icon):
            self.file_label = tb.Label(filename_frame, image=file_icon)
        else:
            self.file_label = tb.Label(filename_frame, text=str(file_icon))
        self.file_label.pack(side=LEFT, padx=(0, 8))
        create_info_tooltip(self.file_label, "Nome do arquivo")

        tb.Label(filename_frame, text="Nome do arquivo:").pack(side=LEFT, padx=(0, 8))
        self.filename_var = tk.StringVar(value=self.default_filename)
        self.filename_entry = tb.Entry(filename_frame, textvariable=self.filename_var)
        self.filename_entry.pack(side=LEFT, fill=X, expand=True)
        create_info_tooltip(self.filename_entry, "Nome do arquivo a salvar")

        def on_filename_change(*args):
            if self.save_mode and hasattr(self, "select_btn"):
                if self.filename_var.get().strip():
                    self.select_btn.config(state=NORMAL)
                else:
                    self.select_btn.config(state=DISABLED)

        self.filename_var.trace_add("write", on_filename_change)

        if self.save_mode and hasattr(self, "select_btn"):
            if self.filename_var.get().strip():
                self.select_btn.config(state=NORMAL)

    def create_action_buttons(self, parent):
        """Cria os botões de ação (Cancelar e Selecionar/Salvar)"""
        button_frame = tb.Frame(parent)
        button_frame.pack(fill=X)

        cancel_icon = self.icon_manager.get_icon('cancel', size=(20, 20))
        if self.icon_manager.is_image_icon(cancel_icon):
            cancel_btn = tb.Button(
                button_frame,
                image=cancel_icon,
                text="Cancelar",
                compound=LEFT,
                command=self.cancel_selection,
                bootstyle=SECONDARY,
                width=16,
            )
        else:
            cancel_btn = tb.Button(
                button_frame,
                text=f"{cancel_icon} Cancelar",
                command=self.cancel_selection,
                bootstyle=SECONDARY,
                width=16,
            )
        cancel_btn.pack(side=RIGHT, padx=(8, 0))
        create_info_tooltip(cancel_btn, "Cancelar e fechar o explorador")

        if self.select_folder:
            action_icon = self.icon_manager.get_icon('select', size=(20, 20))
            action_text = "Selecionar Pasta"
        elif self.save_mode:
            action_icon = self.icon_manager.get_icon('save', size=(20, 20))
            action_text = "Salvar"
        else:
            action_icon = self.icon_manager.get_icon('select', size=(20, 20))
            action_text = "Selecionar"

        self.select_btn = tb.Button(
            button_frame,
            command=self.confirm_selection,
            bootstyle=PRIMARY,
            width=16,
        )
        
        if self.icon_manager.is_image_icon(action_icon):
            self.select_btn.configure(image=action_icon, text=action_text, compound=LEFT)
        else:
            self.select_btn.configure(text=f"{action_icon} {action_text}")
            
        self.select_btn.pack(side=RIGHT, padx=(8, 0))

        if self.save_mode:
            if hasattr(self, "filename_var") and self.filename_var.get():
                self.select_btn.config(state=NORMAL)
            else:
                self.select_btn.config(state=DISABLED)
        elif self.select_folder:
            self.select_btn.config(state=NORMAL)
        else:
            self.select_btn.config(state=DISABLED)

        create_info_tooltip(self.select_btn, "Confirmar seleção")

    def load_directory(self, path: str):
        """Carrega o conteúdo do diretório especificado"""
        try:
            if not os.path.exists(path) or not os.path.isdir(path):
                show_error(self, f"Diretório não encontrado: {path}")
                return

            # Verifica se o caminho é acessível
            if not self.config.is_path_accessible(path):
                show_warning(self, f"Sem permissão para acessar: {path}\n\nTentando um diretório alternativo...")
                # Tenta navegar para um diretório acessível
                accessible_parent = self.find_accessible_parent(path)
                if accessible_parent and accessible_parent != path:
                    self.load_directory(accessible_parent)
                    return
                else:
                    show_error(self, f"Não foi possível acessar o diretório: {path}")
                    return

            if not self.history or self.history[self.history_index] != path:
                self.history = self.history[: self.history_index + 1]
                self.history.append(path)
                self.history_index = len(self.history) - 1

            self.current_path = path
            self.address_var.set(path)

            for item in self.treeview.get_children():
                self.treeview.delete(item)

            items = os.listdir(path)
            folders = []
            files = []

            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    # Filtra pastas virtuais e links duplicados no Windows
                    if not self.is_virtual_folder_duplicate(item, full_path):
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

            # Salva o caminho atual apenas se for acessível
            if self.config.is_path_accessible(path):
                self.config.save_last_path(path)

        except PermissionError:
            show_error(self, f"Sem permissão para acessar: {path}")
            # Tenta navegar para um diretório acessível
            accessible_parent = self.find_accessible_parent(path)
            if accessible_parent and accessible_parent != path:
                self.load_directory(accessible_parent)
        except Exception as e:
            show_error(self, f"Erro ao carregar diretório: {str(e)}")

    def is_virtual_folder_duplicate(self, folder_name, full_path):
        """Verifica se é uma pasta virtual duplicada no Windows"""
        if os.name != 'nt':
            return False
        
        try:
            # Lista de nomes de pastas virtuais problemáticas
            virtual_names = {
                'meus documentos', 'my documents',
                'minhas imagens', 'my pictures', 
                'minha música', 'my music',
                'meus vídeos', 'my videos'
            }
            
            folder_lower = folder_name.lower()
            
            # Se for uma pasta virtual conhecida
            if folder_lower in virtual_names:
                # Verifica se já existe a pasta real correspondente
                real_names = {
                    'meus documentos': 'documents',
                    'my documents': 'documents', 
                    'minhas imagens': 'pictures',
                    'my pictures': 'pictures',
                    'minha música': 'music',
                    'my music': 'music',
                    'meus vídeos': 'videos',
                    'my videos': 'videos'
                }
                
                real_folder_name = real_names.get(folder_lower)
                if real_folder_name:
                    real_folder_path = os.path.join(os.path.dirname(full_path), real_folder_name)
                    if os.path.exists(real_folder_path):
                        # Se a pasta real existe, ignora a virtual
                        return True
            
            # Verifica se é um link simbólico para uma pasta que já existe
            if os.path.islink(full_path):
                try:
                    target_path = os.path.realpath(full_path)
                    target_name = os.path.basename(target_path)
                    
                    # Se o alvo já estiver na lista, ignora o link
                    parent_dir = os.path.dirname(full_path)
                    target_in_parent = os.path.join(parent_dir, target_name)
                    if os.path.exists(target_in_parent):
                        return True
                except OSError:
                    pass
            
            return False
            
        except Exception:
            return False

    def find_accessible_parent(self, path):
        """Encontra um diretório pai acessível"""
        current = path
        while current and current != os.path.dirname(current):
            current = os.path.dirname(current)
            if self.config.is_path_accessible(current):
                return current
        return None

    def filter_file(self, filename: str) -> bool:
        """Filtra arquivos baseado nos tipos de arquivo especificados"""
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
        """Retorna o tamanho do arquivo formatado"""
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
        """Retorna o indicador de pasta"""
        return "Pasta"

    def get_file_modified(self, filepath: str) -> str:
        """Retorna a data de modificação formatada"""
        try:
            mtime = os.path.getmtime(filepath)
            return datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        except:
            return "?"

    def on_item_double_click(self, event=None):
        """Manipula duplo clique em itens da lista"""
        item = self.treeview.selection()
        if item:
            item_id = item[0]
            if item_id == "..":
                self.go_up()
            elif os.path.isdir(item_id):
                # Verifica se o diretório é acessível antes de navegar
                if self.config.is_path_accessible(item_id):
                    self.load_directory(item_id)
                else:
                    show_warning(self, f"Sem permissão para acessar: {item_id}")

    def on_selection_changed(self, event=None):
        """Manipula mudança na seleção de itens"""
        selected = self.treeview.selection()
        self.selected_files = []

        for item_id in selected:
            if item_id != ".." and not os.path.isdir(item_id):
                self.selected_files.append(item_id)

        if self.save_mode and hasattr(self, "filename_var") and self.selected_files:
            filename = os.path.basename(self.selected_files[0])
            self.filename_var.set(filename)

        if self.select_folder:
            self.select_btn.config(state=NORMAL)
        elif self.save_mode:
            if hasattr(self, "filename_var") and self.filename_var.get().strip():
                self.select_btn.config(state=NORMAL)
            else:
                self.select_btn.config(state=DISABLED)
        else:
            self.select_btn.config(state=NORMAL if self.selected_files else DISABLED)

    def on_address_changed(self, event=None):
        """Manipula mudança no endereço da barra de endereço"""
        new_path = self.address_var.get()
        if os.path.isdir(new_path) and self.config.is_path_accessible(new_path):
            self.load_directory(new_path)
        else:
            show_error(self, "Diretório não encontrado ou sem permissão de acesso")
            self.address_var.set(self.current_path)

    def on_search(self, event=None):
        """Manipula pesquisa em tempo real"""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.load_directory(self.current_path)
            return

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
        """Navega para o diretório anterior no histórico"""
        if self.history_index > 0:
            self.history_index -= 1
            self.load_directory(self.history[self.history_index])

    def go_forward(self):
        """Navega para o próximo diretório no histórico"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.load_directory(self.history[self.history_index])

    def go_up(self):
        """Navega para o diretório pai"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path and self.config.is_path_accessible(parent):
            self.load_directory(parent)
        elif parent != self.current_path:
            show_warning(self, f"Sem permissão para acessar: {parent}")

    def go_home(self):
        """Navega para o diretório home do usuário"""
        home_path = os.path.expanduser("~")
        if self.config.is_path_accessible(home_path):
            self.load_directory(home_path)
        else:
            show_warning(self, f"Sem permissão para acessar: {home_path}")

    def refresh_directory(self):
        """Recarrega o diretório atual"""
        self.load_directory(self.current_path)

    def create_new_folder(self):
        """Cria uma nova pasta no diretório atual"""
        # Verifica se temos permissão de escrita no diretório atual
        if not self.config.is_path_accessible(self.current_path):
            show_error(self, "Sem permissão para criar pastas neste diretório")
            return

        folder_name = self._prompt_for_new_folder_name(default="Nova Pasta")
        if folder_name is None:
            return

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
        """Diálogo para obter o nome da nova pasta"""
        dlg = tb.Toplevel(self)
        dlg.title("Criar Pasta")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=15)
        frm.pack(fill=BOTH, expand=True)

        folder_icon = self.icon_manager.get_icon('folder', size=(20, 20))

        if self.icon_manager.is_image_icon(folder_icon):
            icon_label = tb.Label(frm, image=folder_icon)
        else:
            icon_label = tb.Label(frm, text=str(folder_icon))
        icon_label.pack(side=LEFT, padx=(0, 8))

        tb.Label(frm, text="Nome da nova pasta:", font=("Helvetica", 11)).pack(
            anchor="w", pady=(0, 8)
        )
        name_var = tk.StringVar(value=default)
        entry = tb.Entry(frm, textvariable=name_var, width=30)
        entry.pack(fill=X, pady=(0, 10))
        entry.focus_set()

        try:
            entry.selection_range(0, tk.END)
        except Exception:
            pass

        btn_frame = tb.Frame(frm)
        btn_frame.pack(fill=X, pady=(8, 0))

        result = {"value": None}

        def on_ok():
            result["value"] = name_var.get()
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        create_icon = self.icon_manager.get_icon('select', size=(18, 18))
        
        if self.icon_manager.is_image_icon(create_icon):
            ok_btn = tb.Button(
                btn_frame,
                image=create_icon,
                text=" Criar",
                compound=LEFT,
                bootstyle=SUCCESS,
                command=on_ok
            )
        else:
            ok_btn = tb.Button(
                btn_frame,
                text=f"{create_icon} Criar",
                bootstyle=SUCCESS,
                command=on_ok
            )
        ok_btn.pack(side=LEFT, padx=8, fill=X, expand=True)

        cancel_icon = self.icon_manager.get_icon('cancel', size=(18, 18))
        
        if self.icon_manager.is_image_icon(cancel_icon):
            cancel_btn = tb.Button(
                btn_frame,
                image=cancel_icon,
                text=" Cancelar",
                compound=LEFT,
                bootstyle=SECONDARY,
                command=on_cancel
            )
        else:
            cancel_btn = tb.Button(
                btn_frame,
                text=f"{cancel_icon} Cancelar",
                bootstyle=SECONDARY,
                command=on_cancel
            )
        cancel_btn.pack(side=LEFT, padx=8, fill=X, expand=True)

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

    def confirm_selection(self):
        """Confirma a seleção atual"""
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
        """Cancela a seleção e fecha o explorador"""
        self.selected_files = []
        self.destroy()

    def update_navigation_buttons(self):
        """Atualiza o estado dos botões de navegação"""
        self.back_btn.config(state=NORMAL if self.history_index > 0 else DISABLED)
        self.forward_btn.config(
            state=NORMAL if self.history_index < len(self.history) - 1 else DISABLED
        )
        self.up_btn.config(
            state=(
                NORMAL
                if self.current_path != os.path.dirname(self.current_path) and 
                   self.config.is_path_accessible(os.path.dirname(self.current_path))
                else DISABLED
            )
        )

    def center_window(self):
        """Centraliza a janela na tela"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


# Funções de conveniência para uso externo
def askopenfilename(
    parent, title="Abrir arquivo", initialfile="", filetypes=None, select_multiple=False
):
    """Abre o explorador para selecionar um arquivo"""
    if initialfile and os.path.isdir(
        os.path.dirname(initialfile) if os.path.dirname(initialfile) else ""
    ):
        initial_folder = os.path.dirname(initialfile)
    else:
        initial_folder = None

    filetypes = filetypes or [("Todos os arquivos", "*.*")]
    browser = FileBrowser(
        parent,
        title=title,
        initial_folder=initial_folder,
        file_types=filetypes,
        select_multiple=select_multiple,
    )
    
    if select_multiple:
        return browser.selected_files
    else:
        return browser.selected_files[0] if browser.selected_files else ""


def askdirectory(parent, title="Selecionar pasta", initialdir=None):
    """Abre o explorador para selecionar uma pasta"""
    browser = FileBrowser(
        parent, title=title, initial_folder=initialdir, select_folder=True
    )
    return browser.selected_files[0] if browser.selected_files else ""


def asksaveasfilename(
    parent,
    title="Salvar arquivo",
    initialfile="",
    filetypes=None,
    defaultextension="",
):
    """Abre o explorador para salvar um arquivo"""
    if initialfile and os.path.isdir(
        os.path.dirname(initialfile) if os.path.dirname(initialfile) else ""
    ):
        initial_folder = os.path.dirname(initialfile)
    else:
        initial_folder = None

    filetypes = filetypes or [("Todos os arquivos", "*.*")]
    browser = FileBrowser(
        parent,
        title=title,
        initial_folder=initial_folder,
        file_types=filetypes,
        save_mode=True,
        default_filename=os.path.basename(initialfile) if initialfile else "",
    )
    return browser.selected_files[0] if browser.selected_files else ""