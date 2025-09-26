# core/utils.py
"""
Utilitários para formatação e validação de dados.
Funções auxiliares para manipulação de datas, valores monetários e outros formatos.
"""

import re
from datetime import datetime
from typing import Optional, Union


# ==============================================
# FUNÇÕES DE MOEDA CORRIGIDAS
# ==============================================


def formatar_moeda(valor: Union[str, float, int], com_simbolo: bool = True) -> str:
    """
    Corrigido: Agora lida corretamente com valores inteiros e decimais
    """
    try:
        # Se for número, converte para string
        if isinstance(valor, (int, float)):
            valor_str = str(valor)
        else:
            valor_str = str(valor).strip()

        # Remove possíveis símbolos de moeda e espaços
        valor_str = re.sub(r"[^\d,.]", "", valor_str)

        # Se estiver vazio, retorna zero
        if not valor_str:
            return "R$ 0,00" if com_simbolo else "0,00"

        # Verifica se tem vírgula (formato brasileiro)
        if "," in valor_str:
            # Se tem ponto e vírgula, assume que ponto é separador de milhar
            if "." in valor_str:
                # Remove pontos (separadores de milhar) e substitui vírgula por ponto
                valor_str = valor_str.replace(".", "").replace(",", ".")
            else:
                # Apenas substitui vírgula por ponto
                valor_str = valor_str.replace(",", ".")

        # Converte para float
        valor_float = float(valor_str)

        # Formata com 2 casas decimais
        if valor_float.is_integer():
            formatado = f"{int(valor_float):,}".replace(",", ".")
            formatado = f"{formatado},00"
        else:
            formatado = (
                f"{valor_float:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        return f"R$ {formatado}" if com_simbolo else formatado

    except (ValueError, TypeError):
        return "R$ 0,00" if com_simbolo else "0,00"


def converter_para_decimal(valor: Union[str, float, int]) -> float:
    """
    Corrigido: Conversão mais robusta para valores monetários
    """
    try:
        if isinstance(valor, (int, float)):
            return round(float(valor), 2)

        valor_str = str(valor).strip()

        # Remove tudo exceto dígitos, vírgula e ponto
        valor_limpo = re.sub(r"[^\d,.]", "", valor_str)

        if not valor_limpo:
            return 0.00

        # Analisa o formato
        if "," in valor_limpo and "." in valor_limpo:
            # Formato: 1.234,56 (ponto é milhar, vírgula é decimal)
            partes = valor_limpo.split(",")
            if len(partes) == 2:
                inteiro = partes[0].replace(".", "")
                decimal = partes[1]
                valor_float = float(f"{inteiro}.{decimal}")
            else:
                # Formato inválido, tenta melhor esforço
                valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                valor_float = float(valor_limpo)
        elif "," in valor_limpo:
            # Formato: 1234,56 (vírgula como decimal)
            valor_float = float(valor_limpo.replace(",", "."))
        elif "." in valor_limpo:
            # Verifica se o ponto é decimal ou milhar
            partes = valor_limpo.split(".")
            if len(partes) > 2:
                # Provavelmente é milhar (1.234.567)
                valor_float = float(valor_limpo.replace(".", ""))
            else:
                # Pode ser decimal (1234.56)
                valor_float = float(valor_limpo)
        else:
            # Apenas dígitos, assume valor inteiro
            valor_float = float(valor_limpo)

        return round(valor_float, 2)

    except (ValueError, TypeError):
        return 0.00


def validar_moeda(valor: str) -> bool:
    """
    Validação mais flexível para formato monetário
    """
    if not valor:
        return False

    # Padrões aceitáveis:
    # - 1234,56
    # - 1.234,56
    # - 1234.56
    # - R$ 1.234,56
    # - Apenas números
    padrao = r"^R?\$?\s*(\d{1,3}(?:\.?\d{3})*(?:[,.]\d{1,2})?|\d+([,.]\d{1,2})?)$"
    return re.match(padrao, valor.strip()) is not None


# ==============================================
# FUNÇÕES DE DATA (MANTIDAS)
# ==============================================


def validar_data(data_str: str) -> bool:
    """
    Valida se uma string está no formato de data DD/MM/AAAA.

    Args:
        data_str: String a ser validada

    Returns:
        True se o formato é válido, False caso contrário
    """
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def formatar_data_sql(data_str: str) -> Optional[str]:
    """
    Converte uma data no formato DD/MM/AAAA para YYYY-MM-DD (formato SQL).

    Args:
        data_str: Data no formato DD/MM/AAAA

    Returns:
        Data no formato YYYY-MM-DD ou None se inválida
    """
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return data_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None


# ==============================================
# FUNÇÕES DE FORMATAÇÃO EM TEMPO REAL (ATUALIZADAS)
# ==============================================


def formatar_valor_digitacao(valor: str) -> str:
    """Aceita apenas números e vírgula durante a digitação"""
    if valor:
        # Permite números, vírgula e ponto (para digitação livre)
        return re.sub(r"[^\d,.]", "", valor)
    return valor


def aplicar_formatacao_valor_final(valor: str) -> str:
    """Formata valor quando perde o foco"""
    if valor:
        return formatar_moeda(valor, com_simbolo=False)
    return valor


# ==============================================
# FUNÇÕES DE VALIDAÇÃO (MANTIDAS)
# ==============================================


def validar_numero_nota(numero: str) -> bool:
    """Valida que contém apenas números"""
    return numero.isdigit() if numero else False


def validar_telefone(telefone: str) -> bool:
    """Valida formato de telefone brasileiro"""
    if not telefone:
        return True

    digits = re.sub(r"\D", "", telefone)
    return len(digits) in [10, 11] and digits.isdigit()


def formatar_telefone(telefone: str) -> str:
    """Formata telefone em tempo real"""
    if not telefone:
        return telefone

    digits = re.sub(r"\D", "", telefone)

    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return telefone


def validar_email(email: str) -> bool:
    """Valida formato de email"""
    if not email:
        return True

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ"""
    if not cnpj:
        return True

    digits = re.sub(r"\D", "", cnpj)
    return len(digits) == 14 and digits.isdigit()


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ em tempo real"""
    if not cnpj:
        return cnpj

    digits = re.sub(r"\D", "", cnpj)

    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    else:
        return cnpj


def limpar_numero(texto: str) -> str:
    """Remove todos os caracteres não numéricos"""
    return re.sub(r"\D", "", texto)


def validar_campo_obrigatorio(
    valor: str, nome_campo: str = "campo"
) -> tuple[bool, str]:
    """Valida se um campo obrigatório foi preenchido"""
    if not valor or not valor.strip():
        return False, f"O campo {nome_campo} é obrigatório!"
    return True, ""


def validar_formulario_nota(
    data: str, numero: str, cliente: str, valor: str
) -> tuple[bool, str]:
    """Validação completa do formulário de nota fiscal"""
    # Campos obrigatórios
    if not all([data, numero, cliente, valor]):
        return False, "Preencha todos os campos obrigatórios!"

    # Validações específicas
    if not validar_data(data):
        return False, "Data inválida! Use o formato DD/MM/AAAA."

    if not validar_numero_nota(numero):
        return False, "Número da nota deve conter apenas dígitos!"

    if not validar_moeda(valor):
        return False, "Valor inválido! Use formato como 1234,56 ou 1.234,56."

    # Validação adicional: valor deve ser maior que zero
    try:
        valor_decimal = converter_para_decimal(valor)
        if valor_decimal <= 0:
            return False, "Valor deve ser maior que zero!"
    except Exception:
        return False, "Valor inválido!"

    return True, ""


def validar_formulario_cliente(
    nome: str, telefone: str = "", email: str = "", cnpj: str = ""
) -> tuple[bool, str]:
    """Validação completa do formulário de cliente"""
    # Campo obrigatório
    if not nome or not nome.strip():
        return False, "O campo Nome é obrigatório!"

    # Validações específicas
    if telefone and not validar_telefone(telefone):
        return False, "Telefone inválido! Use (00) 00000-0000 ou (00) 0000-0000"

    if email and not validar_email(email):
        return False, "Email inválido!"

    if cnpj and not validar_cnpj(cnpj):
        return False, "CNPJ inválido! Deve ter 14 dígitos."

    return True, ""


def converter_data_para_ordenacao(data_str):
    """
    Converte string de data no formato DD/MM/YYYY para objeto date para ordenação.
    """
    try:
        if (
            isinstance(data_str, str)
            and len(data_str) == 10
            and data_str[2] == "/"
            and data_str[5] == "/"
        ):
            day, month, year = map(int, data_str.split("/"))
            return datetime.date(year, month, day)
    except (ValueError, IndexError):
        pass
    return data_str  # Retorna original se não puder converter
