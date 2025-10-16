"""
Módulo principal do sistema de gerenciamento de notas fiscais.
Contém as classes e funções fundamentais para o funcionamento do aplicativo.
"""

from .database import Database
from .theme_manager import ThemeManager
from .utils import (
    format_currency,
    convert_to_decimal,
    validate_currency,
    validate_date,
    format_sql_date,
    validate_invoice_number,
    validate_phone,
    format_phone,
    validate_email,
    validate_cnpj,
    format_cnpj,
    clean_number,
    validate_required_field,
    validate_invoice_form,
    validate_customer_form,
)

# Aliases para manter compatibilidade com código existente
# (funções em português que apontam para as funções em inglês)
formatar_moeda = format_currency
converter_para_decimal = convert_to_decimal
validar_moeda = validate_currency
validar_data = validate_date
formatar_data_sql = format_sql_date
validar_numero_nota = validate_invoice_number
validar_telefone = validate_phone
formatar_telefone = format_phone
validar_email = validate_email
validar_cnpj = validate_cnpj
formatar_cnpj = format_cnpj
limpar_numero = clean_number
validar_campo_obrigatorio = validate_required_field
validar_formulario_nota = validate_invoice_form
validar_formulario_cliente = validate_customer_form

__all__ = [
    # Classes principais
    "Database",
    "ThemeManager",
    
    # Funções em inglês (novo padrão)
    "format_currency",
    "convert_to_decimal",
    "validate_currency",
    "validate_date",
    "format_sql_date",
    "validate_invoice_number",
    "validate_phone",
    "format_phone",
    "validate_email",
    "validate_cnpj",
    "format_cnpj",
    "clean_number",
    "validate_required_field",
    "validate_invoice_form",
    "validate_customer_form",
    
    # Aliases em português (para compatibilidade)
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