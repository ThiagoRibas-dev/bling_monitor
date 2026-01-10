"""
Módulo de persistência SQLite para contadores de código e cache
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class BlingDatabase:
    def __init__(self, db_path="bling_data.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager para conexões SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Inicializa tabelas do banco de dados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabela de contadores de código
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_counters (
                    prefix TEXT PRIMARY KEY,
                    last_value INTEGER NOT NULL DEFAULT 0,
                    category_id INTEGER,
                    category_name TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            # Tabela de eventos processados (idempotência webhook)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    product_id INTEGER,
                    processed_at TEXT NOT NULL,
                    payload TEXT
                )
            """)

            # Ordens de Produção
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_orders (
                    order_id INTEGER PRIMARY KEY,
                    order_number TEXT NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT,
                    supplier_id INTEGER,
                    supplier_name TEXT,
                    created_at TEXT NOT NULL,
                    data TEXT
                )
            """)

            # Itens de Produção
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_code TEXT,
                    quantity REAL NOT NULL,
                    unit_price REAL,
                    FOREIGN KEY (order_id) REFERENCES production_orders(order_id)
                )
            """)

            # Pedidos de Compra
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    order_id INTEGER PRIMARY KEY,
                    order_number TEXT NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT,
                    supplier_id INTEGER,
                    supplier_name TEXT,
                    total_value REAL,
                    created_at TEXT NOT NULL,
                    data TEXT
                )
            """)

            # Itens de Compra
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_code TEXT,
                    quantity REAL NOT NULL,
                    unit_price REAL,
                    FOREIGN KEY (order_id) REFERENCES purchase_orders(order_id)
                )
            """)

            # Controle de Sincronização
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_control (
                    sync_type TEXT PRIMARY KEY,
                    last_sync_date TEXT,
                    last_order_date TEXT,
                    total_orders INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            # Índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_product 
                ON processed_events(product_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type 
                ON processed_events(event_type)
            """)

            # Índices para purchase_items
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_purch_product ON purchase_items(product_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_purch_order ON purchase_items(order_id)"
            )

            # Índices para production_items
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_prod_product ON production_items(product_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_prod_order ON production_items(order_id)"
            )

    def get_next_code(self, prefix, category_id=None, category_name=None):
        """
        Obtém o próximo código sequencial para um prefixo.
        Thread-safe via transação SQLite.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tenta incrementar existente
            cursor.execute(
                """
                UPDATE code_counters 
                SET last_value = last_value + 1,
                    updated_at = ?
                WHERE prefix = ?
            """,
                (datetime.now().isoformat(), prefix),
            )

            # Se não existia, cria
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO code_counters 
                    (prefix, last_value, category_id, category_name, updated_at)
                    VALUES (?, 1, ?, ?, ?)
                """,
                    (prefix, category_id, category_name, datetime.now().isoformat()),
                )
                return f"{prefix}00001"

            # Busca valor atualizado
            cursor.execute(
                "SELECT last_value FROM code_counters WHERE prefix = ?", (prefix,)
            )
            row = cursor.fetchone()
            return f"{prefix}{row['last_value']:05d}"

    def get_last_code_value(self, prefix):
        """Retorna o último valor usado para um prefixo."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_value FROM code_counters WHERE prefix = ?", (prefix,)
            )
            row = cursor.fetchone()
            return row["last_value"] if row else 0

    def is_event_processed(self, event_id):
        """Verifica se um evento webhook já foi processado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE event_id = ? LIMIT 1", (event_id,)
            )
            return cursor.fetchone() is not None

    def mark_event_processed(self, event_id, event_type, product_id=None, payload=None):
        """Marca um evento como processado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO processed_events 
                (event_id, event_type, product_id, processed_at, payload)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    event_type,
                    product_id,
                    datetime.now().isoformat(),
                    json.dumps(payload) if payload else None,
                ),
            )

    def get_stats(self):
        """Retorna estatísticas do banco."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM code_counters")
            counters_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM processed_events")
            events_count = cursor.fetchone()["count"]

            cursor.execute("""
                SELECT prefix, last_value, category_name, updated_at 
                FROM code_counters 
                ORDER BY updated_at DESC 
                LIMIT 10
            """)
            recent_counters = [dict(row) for row in cursor.fetchall()]

            return {
                "counters": counters_count,
                "events": events_count,
                "recent_counters": recent_counters,
            }

    def get_last_sync_date(self, sync_type):
        """Obtém a data da última ordem sincronizada."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT last_order_date 
                FROM sync_control 
                WHERE sync_type = ?
            """,
                (sync_type,),
            )
            row = cursor.fetchone()
            return row["last_order_date"] if row else None

    def save_production_orders(self, orders):
        """Salva ordens de produção no banco."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for order in orders:
                # Usar dataInicio ou dataPrevisaoInicio como data principal
                order_date = (
                    order.get("dataInicio")
                    or order.get("dataPrevisaoInicio")
                    or order.get("dataFim")
                    or order.get("dataPrevisaoFinal")
                )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO production_orders 
                    (order_id, order_number, order_date, status, 
                    supplier_id, supplier_name, created_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order.get("id"),
                        order.get("numero"),
                        order_date,
                        order.get("situacao", {}).get("nome"),
                        None,  # Sem supplier_id em produção
                        order.get("responsavel"),
                        datetime.now().isoformat(),
                        json.dumps(order),
                    ),
                )

                # AGORA TEMOS ITENS! Processar cada item
                itens = order.get("itens", [])
                for item in itens:
                    produto = item.get("produto", {})
                    if produto.get("id"):  # Só salvar se tiver ID do produto
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO production_items
                            (order_id, product_id, product_code, quantity, unit_price)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (
                                order.get("id"),
                                produto.get("id"),
                                produto.get("codigo"),
                                item.get("quantidade", 0),
                                0,  # Ordem de produção não tem preço unitário
                            ),
                        )

    def save_purchase_orders(self, orders):
        """Salva pedidos de compra no banco."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for order in orders:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO purchase_orders 
                    (order_id, order_number, order_date, status,
                     supplier_id, supplier_name, total_value, created_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order.get("id"),
                        order.get("numero"),
                        order.get("data"),
                        order.get("situacao", {}).get("valor"),
                        order.get("contato", {}).get("id"),
                        order.get("contato", {}).get("nome"),
                        order.get("total"),
                        datetime.now().isoformat(),
                        json.dumps(order),
                    ),
                )

                for item in order.get("itens", []):
                    produto = item.get("produto", {})
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO purchase_items
                        (order_id, product_id, product_code, quantity, unit_price)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            order.get("id"),
                            produto.get("id"),
                            produto.get("codigo"),
                            item.get("quantidade"),
                            item.get("valor"),
                        ),
                    )

    def update_sync_control(self, sync_type, last_order_date, order_count):
        """Atualiza controle de sincronização."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sync_control
                (sync_type, last_sync_date, last_order_date, total_orders, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    sync_type,
                    datetime.now().isoformat(),
                    last_order_date,
                    order_count,
                    datetime.now().isoformat(),
                ),
            )

    def product_has_entry(self, product_id):
        """Verifica se produto tem entrada no banco local."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verificar em produção
            cursor.execute(
                """
                SELECT po.order_number, po.order_date, pi.quantity, 
                    po.supplier_name as responsible, 'production' as source
                FROM production_items pi
                JOIN production_orders po ON pi.order_id = po.order_id
                WHERE pi.product_id = ?
                ORDER BY po.order_date DESC
                LIMIT 1
            """,
                (product_id,),
            )

            row = cursor.fetchone()
            if row:
                return True, dict(row)

            # Verificar em compras (mantém igual)
            cursor.execute(
                """
                SELECT po.order_number, po.order_date, pi.quantity, 
                    po.supplier_name, 'purchase' as source
                FROM purchase_items pi
                JOIN purchase_orders po ON pi.order_id = po.order_id
                WHERE pi.product_id = ?
                ORDER BY po.order_date DESC
                LIMIT 1
            """,
                (product_id,),
            )

            row = cursor.fetchone()
            if row:
                return True, dict(row)

            return False, {}
