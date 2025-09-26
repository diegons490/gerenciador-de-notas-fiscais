# gui/utils/__init__.py
"""
Módulo de utilitários para a interface gráfica com ttkbootstrap.
Contém popups personalizados, tabelas customizadas, tooltips e utilitários de interface.

Este arquivo expõe a API pública usada por outras partes da aplicação,
por ex.: `from gui.utils import show_info, asksaveasfilename, create_info_tooltip`
"""

# popups
from .popups import (
    CustomPopup,
    show_info,
    show_warning,
    show_error,
    ask_yes_no,
    ask_ok_cancel,
    ask_retry_cancel,
)

# file browser (explorador)
from .file_browser import FileBrowser, askopenfilename, asksaveasfilename

# tooltips
from .tooltips import (
    ToolTip,
    create_default_tooltip,
    create_warning_tooltip,
    create_error_tooltip,
    create_info_tooltip,
    create_success_tooltip,
)

# lista pública
__all__ = [
    "CustomPopup",
    "show_info",
    "show_warning",
    "show_error",
    "ask_yes_no",
    "ask_ok_cancel",
    "ask_retry_cancel",
    "format_note_row",
    "CustomTable",
    "create_notes_table",
    "create_notes_table_config",
    "FileBrowser",
    "askopenfilename",
    "asksaveasfilename",
    "ToolTip",
    "create_default_tooltip",
    "create_warning_tooltip",
    "create_error_tooltip",
    "create_info_tooltip",
    "create_success_tooltip",
]
