# core/database.py
"""
Gerenciamento completo de banco de dados SQLite para notas fiscais e clientes.
Fornece métodos para CRUD (Create, Read, Update, Delete) de notas e clientes.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional


class Database:
    def __init__(self):
        """
        Inicializa a conexão com o banco de dados e cria as tabelas se não existirem.
        """
        # Verificar se a variável de ambiente está definida
        data_dir = os.environ.get("CONTROLE_NOTAS_DATA_DIR")
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Modo desenvolvimento - usar diretório atual
            self.base_dir = Path(__file__).parent.parent
            self.data_dir = self.base_dir / "data"

        # Criar diretório se não existir
        self.data_dir.mkdir(exist_ok=True)

        self.db_file = self.data_dir / "notas.db"
        self.client_db_file = self.data_dir / "cadastros.db"
        self.config_path = self.data_dir / "config.json"

        self._create_tables()

    def _create_tables(self) -> None:
        """
        Cria as tabelas de notas e clientes se não existirem.
        """
        # Tabela de notas fiscais
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_emissao TEXT NOT NULL,
                    numero TEXT NOT NULL UNIQUE,
                    cliente TEXT NOT NULL,
                    valor REAL NOT NULL,
                    telefone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    cnpj TEXT DEFAULT '',
                    endereco TEXT DEFAULT '',
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

        # Tabela de clientes (CORRIGIDA - removida constraint UNIQUE do CNPJ)
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    telefone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    cnpj TEXT DEFAULT '',
                    endereco TEXT DEFAULT '',
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ativo BOOLEAN DEFAULT 1
                )
            """
            )

    # ==============================================
    # MÉTODOS PARA NOTAS FISCAIS
    # ==============================================

    def insert_nota(
        self,
        data: str,
        numero: str,
        cliente: str,
        valor: float,
        telefone: str = "",
        email: str = "",
        cnpj: str = "",
        endereco: str = "",
    ) -> bool:
        """
        Insere uma nova nota fiscal no banco de dados.

        Args:
            data: Data de emissão no formato YYYY-MM-DD
            numero: Número da nota fiscal
            cliente: Nome do cliente
            valor: Valor da nota fiscal
            telefone: Telefone do cliente (opcional)
            email: Email do cliente (opcional)
            cnpj: CNPJ do cliente (opcional)
            endereco: Endereço do cliente (opcional)

        Returns:
            True se a inserção foi bem-sucedida, False se o número já existe
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO notas (
                        data_emissao, numero, cliente, valor,
                        telefone, email, cnpj, endereco
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (data, numero, cliente, valor, telefone, email, cnpj, endereco),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_notas_por_periodo(self, inicio: str, fim: str) -> List[Tuple]:
        """
        Retorna notas fiscais dentro de um período específico.

        Args:
            inicio: Data inicial no formato YYYY-MM-DD
            fim: Data final no formato YYYY-MM-DD

        Returns:
            Lista de tuplas com informações das notas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    strftime('%d/%m/%Y', data_emissao) AS data_br,
                    numero,
                    cliente,
                    valor
                FROM notas
                WHERE data_emissao BETWEEN ? AND ?
                ORDER BY data_emissao DESC
            """,
                (inicio, fim),
            )
            return cursor.fetchall()

    def get_nota_por_id(self, id_nota: int) -> Optional[Tuple]:
        """
        Retorna uma nota fiscal específica pelo ID.

        Args:
            id_nota: ID da nota fiscal

        Returns:
            Tupla com os dados da nota ou None se não encontrada
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    strftime('%d/%m/%Y', data_emissao) AS data_emissao,
                    numero,
                    cliente,
                    valor,
                    COALESCE(telefone, ''),
                    COALESCE(email, ''),
                    COALESCE(cnpj, ''),
                    COALESCE(endereco, '')
                FROM notas
                WHERE id = ?
            """,
                (id_nota,),
            )
            return cursor.fetchone()

    def get_all_notas(self) -> List[Tuple]:
        """
        Retorna todas as notas fiscais ordenadas por data.

        Returns:
            Lista de tuplas com informações das notas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    strftime('%d/%m/%Y', data_emissao) AS data_br,
                    numero,
                    cliente,
                    valor,
                    telefone,
                    email,
                    cnpj,
                    endereco
                FROM notas
                ORDER BY data_emissao DESC
                """
            )
            return cursor.fetchall()

    def get_total_notas(self) -> int:
        """
        Retorna o total de notas fiscais no sistema.

        Returns:
            Número total de notas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notas")
            return cursor.fetchone()[0]

    def delete_nota(self, id_nota: int) -> None:
        """
        Exclui uma nota fiscal pelo ID.

        Args:
            id_nota: ID da nota fiscal a ser excluída
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notas WHERE id = ?", (id_nota,))

    def delete_all_notas(self) -> None:
        """
        Exclui todas as notas fiscais do sistema.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notas")

    def get_ultima_nota(self) -> Optional[Tuple]:
        """
        Retorna a última nota fiscal inserida.

        Returns:
            Tupla com os dados da última nota ou None se não houver notas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    strftime('%d/%m/%Y', data_emissao) AS data_emissao,
                    numero,
                    cliente,
                    valor
                FROM notas
                ORDER BY id DESC
                LIMIT 1
            """
            )
            return cursor.fetchone()

    def get_notas_por_cliente(self, nome_cliente: str) -> List[Tuple]:
        """
        Retorna notas fiscais de um cliente específico.

        Args:
            nome_cliente: Nome do cliente para filtrar

        Returns:
            Lista de tuplas com informações das notas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    strftime('%d/%m/%Y', data_emissao) AS data_br,
                    numero,
                    cliente,
                    valor
                FROM notas
                WHERE cliente LIKE ?
                ORDER BY data_emissao DESC
            """,
                (f"%{nome_cliente}%",),
            )
            return cursor.fetchall()

    def buscar_notas_por_termo(self, termo: str) -> List[Tuple]:
        """
        Busca notas fiscais por qualquer campo que contenha o termo.

        Args:
            termo: Termo de busca

        Returns:
            Lista de tuplas com informações das notas encontradas
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            term_lower = termo.lower()
            like_text = f"%{term_lower}%"

            like_valor_dot = f"%{termo.replace(',', '.')}%"
            like_valor_comma = f"%{termo.replace('.', ',')}%"

            cursor.execute(
                """
                SELECT
                    id,
                    strftime('%d/%m/%Y', data_emissao) AS data_br,
                    numero,
                    cliente,
                    valor
                FROM notas
                WHERE
                    strftime('%d/%m/%Y', data_emissao) LIKE ? OR
                    LOWER(numero) LIKE ? OR
                    LOWER(cliente) LIKE ? OR
                    LOWER(COALESCE(telefone, '')) LIKE ? OR
                    LOWER(COALESCE(email, '')) LIKE ? OR
                    LOWER(COALESCE(cnpj, '')) LIKE ? OR
                    LOWER(COALESCE(endereco, '')) LIKE ? OR
                    CAST(valor AS TEXT) LIKE ? OR
                    REPLACE(CAST(valor AS TEXT), '.', ',') LIKE ?
                ORDER BY data_emissao DESC
                """,
                (
                    f"%{termo}%",  # data
                    like_text,  # numero
                    like_text,  # cliente
                    like_text,  # telefone
                    like_text,  # email
                    like_text,  # cnpj
                    like_text,  # endereco
                    like_valor_dot,  # valor com ponto
                    like_valor_comma,  # valor com vírgula
                ),
            )
            return cursor.fetchall()

    def update_nota(
        self,
        id_nota: int,
        data: str,
        numero: str,
        cliente: str,
        valor: float,
        telefone: str = "",
        email: str = "",
        cnpj: str = "",
        endereco: str = "",
    ) -> bool:
        """
        Atualiza os dados de uma nota fiscal existente.

        Args:
            id_nota: ID da nota a ser atualizada
            data: Nova data de emissão no formato YYYY-MM-DD
            numero: Novo número da nota fiscal
            cliente: Novo nome do cliente
            valor: Novo valor da nota fiscal
            telefone: Novo telefone do cliente (opcional)
            email: Novo email do cliente (opcional)
            cnpj: Novo CNPJ do cliente (opcional)
            endereco: Novo endereço do cliente (opcional)

        Returns:
            True se a atualização foi bem-sucedida, False se o número já existe
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE notas 
                    SET data_emissao = ?, numero = ?, cliente = ?, valor = ?,
                        telefone = ?, email = ?, cnpj = ?, endereco = ?
                    WHERE id = ?
                    """,
                    (
                        data,
                        numero,
                        cliente,
                        valor,
                        telefone,
                        email,
                        cnpj,
                        endereco,
                        id_nota,
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    # ==============================================
    # MÉTODOS PARA CLIENTES (CORRIGIDOS E COMPLETOS)
    # ==============================================

    def insert_cliente(
        self,
        nome: str,
        telefone: str = "",
        email: str = "",
        cnpj: str = "",
        endereco: str = "",
    ) -> bool:
        """
        Insere um novo cliente no banco de dados.

        Args:
            nome: Nome do cliente (obrigatório, único)
            telefone: Telefone do cliente (opcional)
            email: Email do cliente (opcional)
            cnpj: CNPJ do cliente (opcional)
            endereco: Endereço do cliente (opcional)

        Returns:
            True se a inserção foi bem-sucedida, False se o nome já existe
        """
        try:
            with sqlite3.connect(self.client_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO clientes (nome, telefone, email, cnpj, endereco)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (nome, telefone, email, cnpj, endereco),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_clientes(self) -> List[Tuple]:
        """
        Retorna todos os clientes ativos ordenados por nome.

        Returns:
            Lista de tuplas com (id, nome, telefone, email, cnpj, endereco)
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, nome, telefone, email, cnpj, endereco
                FROM clientes 
                WHERE ativo = 1 
                ORDER BY nome
                """
            )
            return cursor.fetchall()

    def get_cliente_por_id(self, id_cliente: int) -> Optional[Tuple]:
        """
        Retorna um cliente específico pelo ID.

        Args:
            id_cliente: ID do cliente

        Returns:
            Tupla com (id, nome, telefone, email, cnpj, endereco) ou None
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, nome, telefone, email, cnpj, endereco
                FROM clientes 
                WHERE id = ? AND ativo = 1
                """,
                (id_cliente,),
            )
            return cursor.fetchone()

    def get_cliente_por_nome(self, nome: str) -> Optional[Tuple]:
        """
        Retorna um cliente pelo nome exato.

        Args:
            nome: Nome do cliente

        Returns:
            Tupla com (id, nome, telefone, email, cnpj, endereco) ou None
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, nome, telefone, email, cnpj, endereco
                FROM clientes 
                WHERE nome = ? AND ativo = 1
                """,
                (nome,),
            )
            return cursor.fetchone()

    def update_cliente(
        self,
        id_cliente: int,
        nome: str,
        telefone: str = "",
        email: str = "",
        cnpj: str = "",
        endereco: str = "",
    ) -> bool:
        """
        Atualiza os dados de um cliente existente.

        Args:
            id_cliente: ID do cliente a ser atualizado
            nome: Novo nome do cliente
            telefone: Novo telefone do cliente (opcional)
            email: Novo email do cliente (opcional)
            cnpj: Novo CNPJ do cliente (opcional)
            endereco: Novo endereço do cliente (opcional)

        Returns:
            True se a atualização foi bem-sucedida, False se o novo nome já existe
        """
        try:
            with sqlite3.connect(self.client_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE clientes 
                    SET nome = ?, telefone = ?, email = ?, cnpj = ?, endereco = ?
                    WHERE id = ?
                    """,
                    (nome, telefone, email, cnpj, endereco, id_cliente),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_cliente(self, id_cliente: int) -> bool:
        """
        Exclui um cliente (desativa) pelo ID.

        Args:
            id_cliente: ID do cliente a ser excluído

        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            with sqlite3.connect(self.client_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE clientes SET ativo = 0 WHERE id = ?", (id_cliente,)
                )
            return True
        except Exception:
            return False

    def delete_all_clientes(self) -> bool:
        """
        Exclui todos os clientes (desativa).

        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            with sqlite3.connect(self.client_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE clientes SET ativo = 0")
            return True
        except Exception:
            return False

    def search_clientes(self, termo: str) -> List[Tuple]:
        """
        Busca clientes por qualquer campo que contenha o termo.

        Args:
            termo: Termo de busca

        Returns:
            Lista de tuplas com clientes encontrados
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            term_lower = termo.lower()
            like_text = f"%{term_lower}%"

            cursor.execute(
                """
                SELECT id, nome, telefone, email, cnpj, endereco
                FROM clientes
                WHERE 
                    (LOWER(nome) LIKE ? OR
                     LOWER(telefone) LIKE ? OR
                     LOWER(email) LIKE ? OR
                     LOWER(cnpj) LIKE ? OR
                     LOWER(endereco) LIKE ?) 
                    AND ativo = 1
                ORDER BY nome
                """,
                (like_text, like_text, like_text, like_text, like_text),
            )
            return cursor.fetchall()

    def get_total_clientes(self) -> int:
        """
        Retorna o total de clientes ativos no sistema.

        Returns:
            Número total de clientes ativos
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE ativo = 1")
            return cursor.fetchone()[0]

    def cliente_existe(self, nome: str, cnpj: str = "") -> bool:
        """
        Verifica se já existe um cliente com o mesmo nome ou CNPJ.

        Args:
            nome: Nome do cliente a verificar
            cnpj: CNPJ do cliente a verificar (opcional)

        Returns:
            True se o cliente já existe, False caso contrário
        """
        with sqlite3.connect(self.client_db_file) as conn:
            cursor = conn.cursor()

            if cnpj:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM clientes 
                    WHERE (nome = ? OR cnpj = ?) AND ativo = 1
                    """,
                    (nome, cnpj),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM clientes 
                    WHERE nome = ? AND ativo = 1
                    """,
                    (nome,),
                )

            return cursor.fetchone()[0] > 0
