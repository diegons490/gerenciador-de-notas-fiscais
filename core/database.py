# core/database.py
"""
Complete SQLite database management for invoices and customers.
Provides methods for CRUD (Create, Read, Update, Delete) of invoices and customers.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

class Database:
    def __init__(self):
        """
        Initializes database connection and creates tables if they don't exist.
        """
        # Check if environment variable is set
        data_dir = os.environ.get("CONTROLE_NOTAS_DATA_DIR")
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Development mode - use current directory
            self.base_dir = Path(__file__).parent.parent
            self.data_dir = self.base_dir / "data"

        # Create directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

        self.db_file = self.data_dir / "invoices.db"
        self.customer_db_file = self.data_dir / "customers.db"
        self.config_path = self.data_dir / "config.json"

        self._create_tables()

    def _create_tables(self) -> None:
        """
        Creates invoice and customer tables if they don't exist.
        """
        # Invoices table
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_date TEXT NOT NULL,
                    number TEXT NOT NULL UNIQUE,
                    customer TEXT NOT NULL,
                    value REAL NOT NULL,
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    cnpj TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Customers table (CORRECTED - removed UNIQUE constraint from CNPJ)
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    cnpj TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            """)

    # ==============================================
    # INVOICE METHODS
    # ==============================================

    def insert_invoice(self, issue_date: str, number: str, customer: str, value: float,
                      phone: str = "", email: str = "", cnpj: str = "", address: str = "") -> bool:
        """
        Inserts a new invoice into the database.

        Args:
            issue_date: Issue date in YYYY-MM-DD format
            number: Invoice number
            customer: Customer name
            value: Invoice value
            phone: Customer phone (optional)
            email: Customer email (optional)
            cnpj: Customer CNPJ (optional)
            address: Customer address (optional)

        Returns:
            True if insertion successful, False if number already exists
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO invoices (
                        issue_date, number, customer, value,
                        phone, email, cnpj, address
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (issue_date, number, customer, value, phone, email, cnpj, address))
            return True
        except sqlite3.IntegrityError:
            return False

    def get_invoices_by_period(self, start: str, end: str) -> List[Tuple]:
        """
        Returns invoices within a specific period.

        Args:
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format

        Returns:
            List of tuples with invoice information
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    strftime('%d/%m/%Y', issue_date) AS br_date,
                    number,
                    customer,
                    value
                FROM invoices
                WHERE issue_date BETWEEN ? AND ?
                ORDER BY issue_date DESC
            """, (start, end))
            return cursor.fetchall()

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Tuple]:
        """
        Returns a specific invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple with invoice data or None if not found
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    strftime('%d/%m/%Y', issue_date) AS issue_date,
                    number,
                    customer,
                    value,
                    COALESCE(phone, ''),
                    COALESCE(email, ''),
                    COALESCE(cnpj, ''),
                    COALESCE(address, '')
                FROM invoices
                WHERE id = ?
            """, (invoice_id,))
            return cursor.fetchone()

    def get_all_invoices(self) -> List[Tuple]:
        """
        Returns all invoices ordered by date.

        Returns:
            List of tuples with invoice information
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    strftime('%d/%m/%Y', issue_date) AS br_date,
                    number,
                    customer,
                    value,
                    phone,
                    email,
                    cnpj,
                    address
                FROM invoices
                ORDER BY issue_date DESC
            """)
            return cursor.fetchall()

    def get_total_invoices(self) -> int:
        """
        Returns total number of invoices in the system.

        Returns:
            Total number of invoices
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM invoices")
            return cursor.fetchone()[0]

    def delete_invoice(self, invoice_id: int) -> None:
        """
        Deletes an invoice by ID.

        Args:
            invoice_id: ID of invoice to delete
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))

    def delete_all_invoices(self) -> None:
        """
        Deletes all invoices from the system.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices")

    def get_last_invoice(self) -> Optional[Tuple]:
        """
        Returns the last inserted invoice.

        Returns:
            Tuple with last invoice data or None if no invoices
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    strftime('%d/%m/%Y', issue_date) AS issue_date,
                    number,
                    customer,
                    value
                FROM invoices
                ORDER BY id DESC
                LIMIT 1
            """)
            return cursor.fetchone()

    def get_invoices_by_customer(self, customer_name: str) -> List[Tuple]:
        """
        Returns invoices from a specific customer.

        Args:
            customer_name: Customer name to filter

        Returns:
            List of tuples with invoice information
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    strftime('%d/%m/%Y', issue_date) AS br_date,
                    number,
                    customer,
                    value
                FROM invoices
                WHERE customer LIKE ?
                ORDER BY issue_date DESC
            """, (f"%{customer_name}%",))
            return cursor.fetchall()

    def search_invoices_by_term(self, term: str) -> List[Tuple]:
        """
        Searches invoices by any field containing the term.

        Args:
            term: Search term

        Returns:
            List of tuples with found invoice information
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            term_lower = term.lower()
            like_text = f"%{term_lower}%"

            like_value_dot = f"%{term.replace(',', '.')}%"
            like_value_comma = f"%{term.replace('.', ',')}%"

            cursor.execute("""
                SELECT
                    id,
                    strftime('%d/%m/%Y', issue_date) AS br_date,
                    number,
                    customer,
                    value
                FROM invoices
                WHERE
                    strftime('%d/%m/%Y', issue_date) LIKE ? OR
                    LOWER(number) LIKE ? OR
                    LOWER(customer) LIKE ? OR
                    LOWER(COALESCE(phone, '')) LIKE ? OR
                    LOWER(COALESCE(email, '')) LIKE ? OR
                    LOWER(COALESCE(cnpj, '')) LIKE ? OR
                    LOWER(COALESCE(address, '')) LIKE ? OR
                    CAST(value AS TEXT) LIKE ? OR
                    REPLACE(CAST(value AS TEXT), '.', ',') LIKE ?
                ORDER BY issue_date DESC
            """, (
                f"%{term}%",  # date
                like_text,  # number
                like_text,  # customer
                like_text,  # phone
                like_text,  # email
                like_text,  # cnpj
                like_text,  # address
                like_value_dot,  # value with dot
                like_value_comma,  # value with comma
            ))
            return cursor.fetchall()

    def update_invoice(self, invoice_id: int, issue_date: str, number: str, customer: str,
                      value: float, phone: str = "", email: str = "", cnpj: str = "",
                      address: str = "") -> bool:
        """
        Updates data of an existing invoice.

        Args:
            invoice_id: ID of invoice to update
            issue_date: New issue date in YYYY-MM-DD format
            number: New invoice number
            customer: New customer name
            value: New invoice value
            phone: New customer phone (optional)
            email: New customer email (optional)
            cnpj: New customer CNPJ (optional)
            address: New customer address (optional)

        Returns:
            True if update successful, False if number already exists
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE invoices 
                    SET issue_date = ?, number = ?, customer = ?, value = ?,
                        phone = ?, email = ?, cnpj = ?, address = ?
                    WHERE id = ?
                """, (issue_date, number, customer, value, phone, email, cnpj, address, invoice_id))
            return True
        except sqlite3.IntegrityError:
            return False

    # ==============================================
    # CUSTOMER METHODS (CORRECTED AND COMPLETE)
    # ==============================================

    # database.py - método insert_customer
    def insert_customer(self, name: str, phone: str = "", email: str = "",
                    cnpj: str = "", address: str = "") -> bool:
        """
        Inserts a new customer into the database.

        Args:
            name: Customer name (required, unique among active customers)
            phone: Customer phone (optional)
            email: Customer email (optional)
            cnpj: Customer CNPJ (optional)
            address: Customer address (optional)

        Returns:
            True if insertion successful, False if name already exists among active customers
        """
        try:
            with sqlite3.connect(self.customer_db_file) as conn:
                cursor = conn.cursor()
                
                # Check if active customer with same name already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM customers 
                    WHERE name = ? AND active = 1
                """, (name,))
                
                if cursor.fetchone()[0] > 0:
                    return False  # Active customer with same name exists
                
                # Insert new customer
                cursor.execute("""
                    INSERT INTO customers (name, phone, email, cnpj, address)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, phone, email, cnpj, address))
                
                return True
        except sqlite3.IntegrityError:
            return False

    def get_all_customers(self) -> List[Tuple]:
        """
        Returns all active customers ordered by name.

        Returns:
            List of tuples with (id, name, phone, email, cnpj, address)
        """
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, phone, email, cnpj, address
                FROM customers 
                WHERE active = 1 
                ORDER BY name
            """)
            return cursor.fetchall()

    def get_customer_by_id(self, customer_id: int) -> Optional[Tuple]:
        """
        Returns a specific customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Tuple with (id, name, phone, email, cnpj, address) or None
        """
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, phone, email, cnpj, address
                FROM customers 
                WHERE id = ? AND active = 1
            """, (customer_id,))
            return cursor.fetchone()

    def get_customer_by_name(self, name: str) -> Optional[Tuple]:
        """
        Returns a customer by exact name.

        Args:
            name: Customer name

        Returns:
            Tuple with (id, name, phone, email, cnpj, address) or None
        """
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, phone, email, cnpj, address
                FROM customers 
                WHERE name = ? AND active = 1
            """, (name,))
            return cursor.fetchone()

    def update_customer(self, customer_id: int, name: str, phone: str = "",
                       email: str = "", cnpj: str = "", address: str = "") -> bool:
        """
        Updates data of an existing customer.

        Args:
            customer_id: ID of customer to update
            name: New customer name
            phone: New customer phone (optional)
            email: New customer email (optional)
            cnpj: New customer CNPJ (optional)
            address: New customer address (optional)

        Returns:
            True if update successful, False if new name already exists
        """
        try:
            with sqlite3.connect(self.customer_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers 
                    SET name = ?, phone = ?, email = ?, cnpj = ?, address = ?
                    WHERE id = ?
                """, (name, phone, email, cnpj, address, customer_id))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_customer(self, customer_id: int) -> bool:
        """
        Deletes a customer (deactivates) by ID.

        Args:
            customer_id: ID of customer to delete

        Returns:
            True if deletion successful
        """
        try:
            with sqlite3.connect(self.customer_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE customers SET active = 0 WHERE id = ?", (customer_id,))
            return True
        except Exception:
            return False

    def delete_all_customers(self) -> bool:
        """
        Deletes all customers (deactivates).

        Returns:
            True if deletion successful
        """
        try:
            with sqlite3.connect(self.customer_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE customers SET active = 0")
            return True
        except Exception:
            return False

    def search_customers(self, term: str) -> List[Tuple]:
        """
        Searches customers by any field containing the term.

        Args:
            term: Search term

        Returns:
            List of tuples with found customers
        """
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            term_lower = term.lower()
            like_text = f"%{term_lower}%"

            cursor.execute("""
                SELECT id, name, phone, email, cnpj, address
                FROM customers
                WHERE 
                    (LOWER(name) LIKE ? OR
                     LOWER(phone) LIKE ? OR
                     LOWER(email) LIKE ? OR
                     LOWER(cnpj) LIKE ? OR
                     LOWER(address) LIKE ?) 
                    AND active = 1
                ORDER BY name
            """, (like_text, like_text, like_text, like_text, like_text))
            return cursor.fetchall()

    def get_total_customers(self) -> int:
        """
        Returns total number of active customers in the system.

        Returns:
            Total number of active customers
        """
        with sqlite3.connect(self.customer_db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers WHERE active = 1")
            return cursor.fetchone()[0]
