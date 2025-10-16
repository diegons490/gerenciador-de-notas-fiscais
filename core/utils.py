# core/utils.py
"""
Utilities for data formatting and validation.
Helper functions for handling dates, monetary values and other formats.
"""

import re
from datetime import datetime
from typing import Optional, Union


def format_currency(value: Union[str, float, int], with_symbol: bool = True) -> str:
    """Formats monetary value to Brazilian format."""
    try:
        if isinstance(value, (int, float)):
            value_float = float(value)
        else:
            value_str = str(value).strip()
            
            # Remove tudo que não é dígito, ponto ou vírgula
            value_str = re.sub(r"[^\d,.]", "", value_str)
            
            if not value_str:
                return "R$ 0,00" if with_symbol else "0,00"
            
            # Se tem vírgula e ponto, trata ponto como separador de milhar
            if "," in value_str and "." in value_str:
                # Remove os pontos (separadores de milhar) e substitui vírgula por ponto
                value_str = value_str.replace(".", "").replace(",", ".")
            # Se só tem vírgula, trata como decimal
            elif "," in value_str:
                value_str = value_str.replace(",", ".")
            # Se só tem ponto, verifica se é separador de milhar ou decimal
            elif "." in value_str:
                parts = value_str.split(".")
                # Se a parte após o último ponto tem 3 dígitos, provavelmente é separador de milhar
                if len(parts) > 1 and len(parts[-1]) == 3:
                    value_str = value_str.replace(".", "")
                # Senão, trata como decimal
                else:
                    # Se tem múltiplos pontos, é separador de milhar
                    if value_str.count(".") > 1:
                        value_str = value_str.replace(".", "")
                    # Senão, mantém como está (será tratado como decimal)
            
            value_float = float(value_str)

        # Formata para o padrão brasileiro
        value_str_formatted = f"{value_float:,.2f}"
        
        # Substitui as formatações padrão do Python pelo padrão brasileiro
        parts = value_str_formatted.split(".")
        integer_part = parts[0].replace(",", "X").replace(".", ",").replace("X", ".")
        decimal_part = parts[1] if len(parts) > 1 else "00"
        
        formatted = f"{integer_part},{decimal_part}"
        
        return f"R$ {formatted}" if with_symbol else formatted

    except (ValueError, TypeError):
        return "R$ 0,00" if with_symbol else "0,00"


def convert_to_decimal(value: Union[str, float, int]) -> float:
    """Converts monetary value to decimal."""
    try:
        if isinstance(value, (int, float)):
            return round(float(value), 2)

        value_str = str(value).strip()
        clean_value = re.sub(r"[^\d,.]", "", value_str)

        if not clean_value:
            return 0.00

        # Se tem vírgula e ponto, trata ponto como separador de milhar
        if "," in clean_value and "." in clean_value:
            # Remove os pontos (separadores de milhar) e substitui vírgula por ponto
            clean_value = clean_value.replace(".", "").replace(",", ".")
        # Se só tem vírgula, trata como decimal
        elif "," in clean_value:
            clean_value = clean_value.replace(",", ".")
        # Se só tem ponto, verifica se é separador de milhar
        elif "." in clean_value:
            parts = clean_value.split(".")
            # Se tem múltiplos pontos ou a parte após o último ponto tem 3 dígitos, é separador de milhar
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                clean_value = clean_value.replace(".", "")
            # Senão, mantém como decimal
            # (não faz nada, pois o ponto já será tratado como decimal pelo float)

        value_float = float(clean_value)
        return round(value_float, 2)

    except (ValueError, TypeError):
        return 0.00


def validate_currency(value: str) -> bool:
    """Validates Brazilian currency format."""
    if not value:
        return False
    
    # Remove espaços e símbolos de real
    clean_value = re.sub(r"[R\$\s]", "", value.strip())
    
    # Padrões aceitos:
    # 1234,56
    # 1.234,56
    # 1234
    # 1.234
    pattern = r"^\d{1,3}(?:\.?\d{3})*(?:,\d{1,2})?$"
    return re.match(pattern, clean_value) is not None


def validate_date(date_str: str) -> bool:
    """Validates date in DD/MM/YYYY format."""
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def format_sql_date(date_str: str) -> Optional[str]:
    """Converts date from DD/MM/YYYY to YYYY-MM-DD format."""
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None


def format_typing_value(value: str) -> str:
    """Formats value during typing to allow proper Brazilian currency input."""
    if not value:
        return value
    
    # Permite apenas dígitos, pontos e vírgulas
    cleaned = re.sub(r"[^\d,.]", "", value)
    
    # Se não tem vírgula, formata como número inteiro com separadores de milhar
    if "," not in cleaned:
        # Remove todos os pontos existentes
        without_dots = cleaned.replace(".", "")
        if without_dots:
            try:
                # Converte para número e formata com separadores de milhar
                number = int(without_dots)
                formatted = f"{number:,}".replace(",", ".")
                return formatted
            except (ValueError, TypeError):
                return cleaned
    
    return cleaned


def apply_final_value_format(value: str) -> str:
    """Applies final formatting to value when focus is lost."""
    if not value:
        return value
    
    # Usa a função principal de formatação sem o símbolo
    return format_currency(value, with_symbol=False)


def validate_invoice_number(number: str) -> bool:
    """Validates invoice number contains only digits."""
    return number.isdigit() if number else False


def validate_phone(phone: str) -> bool:
    """Validates Brazilian phone format."""
    if not phone:
        return True

    digits = re.sub(r"\D", "", phone)
    return len(digits) in [10, 11] and digits.isdigit()


def format_phone(phone: str) -> str:
    """Formats phone number in real time."""
    if not phone:
        return phone
    
    digits = re.sub(r"\D", "", phone)
    
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return phone


def validate_email(email: str) -> bool:
    """Validates email format."""
    if not email:
        return True

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_cnpj(cnpj: str) -> bool:
    """Validates CNPJ format."""
    if not cnpj:
        return True

    digits = re.sub(r"\D", "", cnpj)
    return len(digits) == 14 and digits.isdigit()


def format_cnpj(cnpj: str) -> str:
    """Formats CNPJ in real time."""
    if not cnpj:
        return cnpj
    
    digits = re.sub(r"\D", "", cnpj)
    
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    else:
        return cnpj


def clean_number(text: str) -> str:
    """Removes all non-numeric characters."""
    return re.sub(r"\D", "", text)


def validate_required_field(value: str, field_name: str = "campo") -> tuple[bool, str]:
    """Validates required field."""
    if not value or not value.strip():
        return False, f"O campo {field_name} é obrigatório!"
    return True, ""


def validate_invoice_form(date: str, number: str, customer: str, value: str) -> tuple[bool, str]:
    """Validates complete invoice form."""
    if not all([date, number, customer, value]):
        return False, "Preencha todos os campos obrigatórios!"

    if not validate_date(date):
        return False, "Data inválida! Use o formato DD/MM/AAAA."

    if not validate_invoice_number(number):
        return False, "Número da nota deve conter apenas dígitos!"

    if not validate_currency(value):
        return False, "Valor inválido! Use formato como 1234,56 ou 1.234,56."

    try:
        value_decimal = convert_to_decimal(value)
        if value_decimal <= 0:
            return False, "Valor deve ser maior que zero!"
    except Exception:
        return False, "Valor inválido!"

    return True, ""


def validate_customer_form(name: str, phone: str = "", email: str = "", cnpj: str = "") -> tuple[bool, str]:
    """Validates complete customer form."""
    if not name or not name.strip():
        return False, "O campo Nome é obrigatório!"

    if phone and not validate_phone(phone):
        return False, "Telefone inválido! Use (00) 00000-0000 ou (00) 0000-0000"

    if email and not validate_email(email):
        return False, "Email inválido!"

    if cnpj and not validate_cnpj(cnpj):
        return False, "CNPJ inválido! Deve ter 14 dígitos."

    return True, ""


def convert_date_for_sorting(date_str):
    """Converts date string to date object for sorting."""
    try:
        if (isinstance(date_str, str) and len(date_str) == 10 
            and date_str[2] == "/" and date_str[5] == "/"):
            day, month, year = map(int, date_str.split("/"))
            return datetime.date(year, month, day)
    except (ValueError, IndexError):
        pass
    return date_str