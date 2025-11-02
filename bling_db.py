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
            
            # Índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_product 
                ON processed_events(product_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type 
                ON processed_events(event_type)
            """)
    
    def get_next_code(self, prefix, category_id=None, category_name=None):
        """
        Obtém o próximo código sequencial para um prefixo.
        Thread-safe via transação SQLite.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tenta incrementar existente
            cursor.execute("""
                UPDATE code_counters 
                SET last_value = last_value + 1,
                    updated_at = ?
                WHERE prefix = ?
            """, (datetime.now().isoformat(), prefix))
            
            # Se não existia, cria
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO code_counters 
                    (prefix, last_value, category_id, category_name, updated_at)
                    VALUES (?, 1, ?, ?, ?)
                """, (prefix, category_id, category_name, datetime.now().isoformat()))
                return f"{prefix}00001"
            
            # Busca valor atualizado
            cursor.execute(
                "SELECT last_value FROM code_counters WHERE prefix = ?",
                (prefix,)
            )
            row = cursor.fetchone()
            return f"{prefix}{row['last_value']:05d}"
    
    def get_last_code_value(self, prefix):
        """Retorna o último valor usado para um prefixo."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_value FROM code_counters WHERE prefix = ?",
                (prefix,)
            )
            row = cursor.fetchone()
            return row['last_value'] if row else 0
    
    def is_event_processed(self, event_id):
        """Verifica se um evento webhook já foi processado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE event_id = ? LIMIT 1",
                (event_id,)
            )
            return cursor.fetchone() is not None
    
    def mark_event_processed(self, event_id, event_type, product_id=None, payload=None):
        """Marca um evento como processado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO processed_events 
                (event_id, event_type, product_id, processed_at, payload)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_id,
                event_type,
                product_id,
                datetime.now().isoformat(),
                json.dumps(payload) if payload else None
            ))
    
    def get_stats(self):
        """Retorna estatísticas do banco."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM code_counters")
            counters_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM processed_events")
            events_count = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT prefix, last_value, category_name, updated_at 
                FROM code_counters 
                ORDER BY updated_at DESC 
                LIMIT 10
            """)
            recent_counters = [dict(row) for row in cursor.fetchall()]
            
            return {
                'counters': counters_count,
                'events': events_count,
                'recent_counters': recent_counters
            }
