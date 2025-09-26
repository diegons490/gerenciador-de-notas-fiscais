# core/theme_manager.py (limpo)
"""
Gerenciador de temas visuais para a aplicação usando ttkbootstrap.
Oferece temas claros, escuros e personalizados com variantes.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.style import ThemeDefinition


class ThemeManager:
    """
    Gerencia temas visuais da aplicação, incluindo temas padrão do ttkbootstrap
    e temas personalizados com variantes claro/escuro.
    """

    def __init__(self, style=None):
        """
        Inicializa o gerenciador de temas, carregando configurações salvas.
        """
        # Configurar diretórios
        self._setup_directories()

        # Carregar configurações
        self.config = self._load_config()

        # Instância do estilo
        self.style = style

        # Carregar temas customizados
        self.custom_themes = self._load_custom_themes()

        # Temas disponíveis
        self.available_themes = self._get_available_themes()
        self.current_theme = self.config.get("theme", "darkly")
        self.current_mode = self.config.get("mode", "dark")

        # Registrar temas customizados (se houver style)
        if self.style:
            self._register_custom_themes()

        # Caminho do ícone
        self.icon_path = self._find_icon_path()

    def _setup_directories(self):
        """Configura os diretórios de dados da aplicação."""
        # Diretório de dados (env ou dev)
        data_dir = os.environ.get("CONTROLE_NOTAS_DATA_DIR")
        if data_dir:
            self.data_dir = Path(data_dir)
            self.base_dir = Path(data_dir).parent
        else:
            # Modo desenvolvimento
            self.base_dir = Path(__file__).parent.parent
            self.data_dir = self.base_dir / "data"

        self.data_dir.mkdir(exist_ok=True)
        self.config_path = self.data_dir / "config.json"

        # Diretório de temas customizados
        self.custom_themes_dir = self.base_dir / "gui" / "custom-themes"
        self.custom_themes_dir.mkdir(exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega as configurações salvas do arquivo JSON.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # Garantir que todas as chaves necessárias existam
                    default_config = self._get_default_config()
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                return self._get_default_config()

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna as configurações padrão."""
        return {
            "theme": "darkly",
            "mode": "dark",
            "window_size": [1200, 800],
            "window_position": [100, 100],
            "window_maximized": False,
            "window_state": "normal",
        }

    def save_config(self):
        """Salva as configurações atuais no arquivo JSON."""
        try:
            self.data_dir.mkdir(exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def save_window_state(self, window):
        """Salva o estado atual da janela."""
        try:
            # Verificar se a janela está maximizada
            try:
                is_zoomed = window.state() == "zoomed"
            except:
                is_zoomed = window.attributes("-zoomed")

            self.config["window_maximized"] = is_zoomed
            self.config["window_state"] = "maximized" if is_zoomed else "normal"

            # SEMPRE salvar o tamanho e posição atual
            current_width = window.winfo_width()
            current_height = window.winfo_height()
            current_x = window.winfo_x()
            current_y = window.winfo_y()

            if current_width > 0 and current_height > 0:
                self.config["window_size"] = [current_width, current_height]

            if current_x >= 0 and current_y >= 0:
                self.config["window_position"] = [current_x, current_y]

            self.save_config()
        except Exception as e:
            print(f"Erro ao salvar estado da janela: {e}")

    def restore_window_state(self, window):
        """Restaura o estado salvo da janela."""
        try:
            # Primeiro definir um tamanho padrão como fallback
            window.geometry("1200x800+100+100")
            window.update_idletasks()

            # Restaurar maximizado se estava maximizado
            if self.config.get("window_maximized", False):
                try:
                    window.state("zoomed")
                except:
                    window.attributes("-zoomed", True)
            else:
                # Restaurar tamanho e posição específicos
                width, height = self.config.get("window_size", [1200, 800])
                x, y = self.config.get("window_position", [100, 100])

                # Garantir valores mínimos
                width = max(800, width)
                height = max(600, height)

                # Garantir que a janela não fique fora da tela
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()

                x = max(0, min(x, screen_width - width))
                y = max(0, min(y, screen_height - height))

                window.geometry(f"{width}x{height}+{x}+{y}")

            window.update_idletasks()
        except Exception as e:
            print(f"Erro ao restaurar estado da janela: {e}")
            window.geometry("1200x800+100+100")

    def _load_custom_themes(self) -> Dict[str, Dict]:
        """
        Carrega temas customizados da pasta custom-themes no formato JSON.
        """
        custom_themes = {}

        if not self.custom_themes_dir.exists():
            return custom_themes

        for theme_file in self.custom_themes_dir.glob("*.json"):
            try:
                with open(theme_file, "r", encoding="utf-8") as f:
                    theme_data = json.load(f)

                if "themes" in theme_data:
                    for theme_item in theme_data["themes"]:
                        for theme_name, theme_def in theme_item.items():
                            # Garantir que as cores estão no formato dicionário
                            if "colors" in theme_def:
                                colors = theme_def["colors"]
                                if isinstance(colors, list):
                                    colors_dict = {}
                                    for color_item in colors:
                                        if (isinstance(color_item, list) and 
                                            len(color_item) == 2):
                                            key, value = color_item
                                            colors_dict[key] = value
                                    theme_def["colors"] = colors_dict
                                elif not isinstance(colors, dict):
                                    print(f"Formato de cores inválido em {theme_file}")
                                    continue

                            custom_themes[theme_name] = theme_def
                            print(f"Tema customizado carregado: {theme_name}")

            except Exception as e:
                print(f"Erro ao carregar tema customizado de {theme_file}: {e}")

        return custom_themes

    def _register_custom_themes(self):
        """Registra temas customizados no ttkbootstrap."""
        if not self.custom_themes or not self.style:
            return

        try:
            for theme_name, theme_def in self.custom_themes.items():
                try:
                    # Verificar se o tema já está registrado
                    available_themes = self.style.theme_names()
                    if theme_name in available_themes:
                        continue

                    # Garantir que as cores estão no formato correto (dicionário)
                    colors = theme_def.get("colors", {})
                    if isinstance(colors, (list, tuple)):
                        colors_dict = {}
                        for color_tuple in colors:
                            if (isinstance(color_tuple, (list, tuple)) and 
                                len(color_tuple) == 2):
                                key, value = color_tuple
                                colors_dict[key] = value
                        colors = colors_dict

                    if not colors:
                        print(f"Tema {theme_name} não tem cores válidas")
                        continue

                    # Usar o método oficial do ttkbootstrap para registrar temas
                    theme_data = {
                        "type": theme_def.get("type", "light"),
                        "colors": colors
                    }

                    # Criar arquivo JSON temporário para o tema individual
                    import tempfile
                    temp_theme = {"themes": [{theme_name: theme_data}]}

                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        import json
                        json.dump(temp_theme, f, ensure_ascii=False, indent=2)
                        temp_path = f.name

                    try:
                        self.style.load_user_themes(temp_path)
                        print(f"Tema {theme_name} registrado com sucesso")
                    except Exception as e:
                        print(f"Erro ao registrar tema {theme_name} via load_user_themes: {e}")

                        # Fallback: tentar registro direto
                        try:
                            from ttkbootstrap.style import ThemeDefinition
                            theme_definition = ThemeDefinition(
                                name=theme_name,
                                themetype=theme_def.get("type", "light"),
                                colors=colors,
                            )
                            self.style.theme_create(theme_name, theme_definition)
                            print(f"Tema {theme_name} registrado via fallback")
                        except Exception as fallback_error:
                            print(f"Erro fallback ao registrar tema {theme_name}: {fallback_error}")

                    # Limpar arquivo temporário
                    import os
                    os.unlink(temp_path)

                except Exception as e:
                    print(f"Erro ao registrar tema {theme_name}: {e}")
                    continue

        except Exception as e:
            print(f"Erro geral ao registrar temas customizados: {e}")

    def _register_custom_themes_json_method(self):
        """Método alternativo para registrar temas via arquivo JSON"""
        if not self.custom_themes:
            return

        try:
            # Criar arquivo JSON temporário
            temp_json_path = self.custom_themes_dir / "temp_themes.json"
            themes_data = {"themes": []}

            for theme_name, theme_def in self.custom_themes.items():
                # Garantir formato correto das cores
                colors = theme_def.get("colors", {})
                if isinstance(colors, (list, tuple)):
                    colors_dict = {}
                    for color_item in colors:
                        if (
                            isinstance(color_item, (list, tuple))
                            and len(color_item) == 2
                        ):
                            key, value = color_item
                            colors_dict[key] = value
                    theme_def["colors"] = colors_dict

                themes_data["themes"].append({theme_name: theme_def})

            # Salvar arquivo temporário
            with open(temp_json_path, "w", encoding="utf-8") as f:
                json.dump(themes_data, f, indent=2, ensure_ascii=False)

            # Tentar carregar temas usando o método oficial
            try:
                self.style.load_user_themes(str(temp_json_path))
            except Exception as e:
                print(f"Erro com load_user_themes: {e}")

            # Remover arquivo temporário
            if temp_json_path.exists():
                temp_json_path.unlink()

        except Exception as e:
            print(f"Erro no método JSON: {e}")

    def _get_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna todos os temas disponíveis organizados por categoria.
        """
        # Temas built-in do ttkbootstrap
        available_themes = {
            "claro": {
                "name": "Temas Claros",
                "themes": [
                    {"name": "cosmo", "display": "Cosmo", "style": "cosmo"},
                    {"name": "flatly", "display": "Flatly", "style": "flatly"},
                    {"name": "journal", "display": "Journal", "style": "journal"},
                    {"name": "litera", "display": "Litera", "style": "litera"},
                    {"name": "lumen", "display": "Lumen", "style": "lumen"},
                    {"name": "minty", "display": "Minty", "style": "minty"},
                    {"name": "pulse", "display": "Pulse", "style": "pulse"},
                    {"name": "sandstone", "display": "Sandstone", "style": "sandstone"},
                    {"name": "united", "display": "United", "style": "united"},
                    {"name": "yeti", "display": "Yeti", "style": "yeti"},
                    {"name": "morph", "display": "morph", "style": "morph"},
                    {"name": "simplex", "display": "simplex", "style": "simplex"},
                    {"name": "cerculean", "display": "cerculean", "style": "cerculean"},
                    {"name": "united", "display": "united", "style": "united"},
                ],
            },
            "escuro": {
                "name": "Temas Escuros",
                "themes": [
                    {"name": "cyborg", "display": "Cyborg", "style": "cyborg"},
                    {"name": "darkly", "display": "Darkly", "style": "darkly"},
                    {"name": "solar", "display": "Solar", "style": "solar"},
                    {"name": "superhero", "display": "Superhero", "style": "superhero"},
                ],
            },
        }

        # Adicionar temas customizados, se houver
        if self.custom_themes:
            custom_themes_list = []
            for theme_name, theme_def in self.custom_themes.items():
                theme_type = theme_def.get("type", "light")
                theme_type_display = "Claro" if theme_type == "light" else "Escuro"

                custom_themes_list.append(
                    {
                        "name": theme_name,
                        "display": f"{theme_name} ({theme_type_display})",
                        "style": theme_name,
                    }
                )

            if custom_themes_list:
                available_themes["custom"] = {
                    "name": "Temas Customizados",
                    "themes": custom_themes_list,
                }

        return available_themes

    def _find_icon_path(self) -> str:
        """
        Localiza o caminho do ícone da aplicação.
        """
        possible_paths = [
            self.base_dir / "icons" / "GNF.png",
            self.base_dir / "icons" / "controle_de_notas_fiscais.png",
            Path.cwd() / "icons" / "GNF.png",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)
        return ""

    def set_window_icon(self, window):
        """
        Configura o ícone da janela.
        """
        if self.icon_path:
            try:
                icon = tk.PhotoImage(file=self.icon_path)
                window.iconphoto(True, icon)
            except Exception as e:
                print(f"Erro ao carregar ícone: {e}")

    def is_theme_available(self, theme_name: str) -> bool:
        """
        Verifica se um tema está disponível.
        """
        if not self.style:
            return False

        try:
            available_themes = self.style.theme_names()
            return theme_name in available_themes or theme_name in self.custom_themes
        except:
            return theme_name in self.custom_themes

    def get_available_theme(self, preferred_theme: str = None) -> str:
        """
        Retorna um tema disponível, tentando o tema preferido primeiro.
        """
        if not self.style:
            return "darkly"

        # Tentar o tema preferido
        if preferred_theme and self.is_theme_available(preferred_theme):
            return preferred_theme

        # Tentar o tema atual
        if self.is_theme_available(self.current_theme):
            return self.current_theme

        # Tentar temas padrão
        for theme in ["darkly", "cosmo", "flatly"]:
            if self.is_theme_available(theme):
                return theme

        # Último recurso
        try:
            available_themes = self.style.theme_names()
            if available_themes:
                return available_themes[0]
        except:
            pass

        return "darkly"

    def get_theme_names(self) -> List[str]:
        """
        Retorna lista com nomes de todos os temas disponíveis.
        """
        theme_names = []

        if self.style:
            try:
                theme_names.extend(self.style.theme_names())
            except:
                pass

        theme_names.extend(list(self.custom_themes.keys()))
        return list(set(theme_names))

    def get_theme_display_names(self) -> List[Tuple[str, str]]:
        """
        Retorna lista de tuplas (nome, display) para todos os temas.
        """
        theme_list = []
        for category in self.available_themes.values():
            for theme in category["themes"]:
                theme_list.append((theme["name"], theme["display"]))
        return theme_list

    def get_themes_tree_data(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """
        Retorna os temas organizados em árvore por categoria.
        """
        tree_data = []
        for category_key, category_data in self.available_themes.items():
            themes_list = []
            for theme in category_data["themes"]:
                themes_list.append((theme["name"], theme["display"]))
            tree_data.append((category_data["name"], themes_list))
        return tree_data

    def apply_theme(self, theme_name: str, window=None) -> bool:
        """
        Aplica um novo tema à aplicação.
        """
        # Registrar temas customizados se necessário
        if theme_name in self.custom_themes:
            self._register_custom_themes()

        # Verificar se o tema existe
        all_available = set(self.style.theme_names() if self.style else []) | set(
            self.custom_themes.keys()
        )

        if theme_name not in all_available:
            fallback_theme = self.get_available_theme()
            return self.apply_theme(fallback_theme, window)

        self.current_theme = theme_name
        self.config["theme"] = theme_name

        # Determinar modo baseado no tema
        if theme_name in self.custom_themes:
            theme_def = self.custom_themes[theme_name]
            self.current_mode = theme_def.get("type", "dark")
        else:
            claro_themes = [
                t["name"]
                for t in self.available_themes.get("claro", {}).get("themes", [])
            ]
            self.current_mode = "light" if theme_name in claro_themes else "dark"

        self.config["mode"] = self.current_mode
        self.save_config()

        if window and self.style:
            try:
                self.style.theme_use(theme_name)
                return True
            except Exception as e:
                print(f"Erro ao aplicar tema '{theme_name}': {e}")
                try:
                    fallback = self.get_available_theme()
                    self.style.theme_use(fallback)
                    self.current_theme = fallback
                    self.config["theme"] = fallback
                    self.save_config()
                    return True
                except:
                    return False

        return True

    def get_current_theme_colors(self) -> Dict[str, str]:
        """
        Retorna as cores do tema atual.
        """
        if self.current_theme in self.custom_themes:
            theme_def = self.custom_themes[self.current_theme]
            return theme_def.get("colors", {})

        # Cores padrão para temas built-in
        theme_colors = {
            "darkly": {
                "primary": "#375A7F",
                "secondary": "#444444",
                "success": "#00BC8C",
                "info": "#3498DB",
                "warning": "#F39C12",
                "danger": "#E74C3C",
                "light": "#ADB5BD",
                "dark": "#303030",
                "bg": "#222222",
                "fg": "#FFFFFF",
            },
            "cosmo": {
                "primary": "#2780E3",
                "secondary": "#373A3C",
                "success": "#3FB618",
                "info": "#9954BB",
                "warning": "#FF7518",
                "danger": "#FF0039",
                "light": "#F8F9FA",
                "dark": "#373A3C",
                "bg": "#FFFFFF",
                "fg": "#373A3C",
            },
        }

        return theme_colors.get(self.current_theme, theme_colors["darkly"])

    def refresh_custom_themes(self):
        """
        Recarrega os temas customizados da pasta.
        """
        self.custom_themes = self._load_custom_themes()
        self._register_custom_themes()
        self.available_themes = self._get_available_themes()

    def get_custom_themes_dir(self) -> Path:
        """
        Retorna o caminho do diretório de temas customizados.
        """
        return self.custom_themes_dir
