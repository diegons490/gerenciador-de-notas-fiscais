#/file_browser_icons/__init__.py 
"""
Pacote de ícones para o FileBrowser.
Ícones em PNG para interface moderna.
"""

import os

# Lista de ícones disponíveis
ICON_NAMES = [
    'back', 'cancel', 'file', 'folder', 'forward', 'graph', 
    'home', 'new-folder', 'reload', 'save', 'search', 
    'select', 'time', 'up'
]

def get_icon_path(icon_name):
    """Retorna o caminho completo para um ícone"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, f"{icon_name}.png")
    return icon_path

def icon_exists(icon_name):
    """Verifica se um ícone existe"""
    return os.path.exists(get_icon_path(icon_name))