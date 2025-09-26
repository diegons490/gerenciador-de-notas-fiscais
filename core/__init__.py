# core/__init__.py
"""
Módulo principal do sistema de gerenciamento de notas fiscais.
Contém as classes e funções fundamentais para o funcionamento do aplicativo.
"""

from .database import Database
from .theme_manager import ThemeManager
from .utils import (
    formatar_moeda,
    converter_para_decimal,
    validar_moeda,
    validar_data,
    formatar_data_sql,
    validar_numero_nota,
    validar_telefone,
    formatar_telefone,
    validar_email,
    validar_cnpj,
    formatar_cnpj,
    limpar_numero,
    validar_campo_obrigatorio,
    validar_formulario_nota,
    validar_formulario_cliente,
)

__all__ = [
    "Database",
    "ThemeManager",
    "formatar_moeda",
    "converter_para_decimal",
    "validar_moeda",
    "validar_data",
    "formatar_data_sql",
    "validar_numero_nota",
    "validar_telefone",
    "formatar_telefone",
    "validar_email",
    "validar_cnpj",
    "formatar_cnpj",
    "limpar_numero",
    "validar_campo_obrigatorio",
    "validar_formulario_nota",
    "validar_formulario_cliente",
]
