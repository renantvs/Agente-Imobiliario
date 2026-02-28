from typing import List, Optional, Tuple
import psycopg2
import psycopg2.extras
from loguru import logger
from app.core.config import settings


def get_connection() -> psycopg2.extensions.connection:
    """Retorna uma conexão psycopg2 ao PostgreSQL."""
    try:
        conn = psycopg2.connect(settings.POSTGRES_URL)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        raise


def execute_query(sql: str, params: Optional[Tuple] = None) -> List[dict]:
    """Executa uma query SELECT e retorna lista de dicts."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                results = cur.fetchall()
        conn.close()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Erro ao executar query: {e} | SQL: {sql}")
        return []


def execute_write(sql: str, params: Optional[Tuple] = None) -> bool:
    """Executa INSERT, UPDATE ou DELETE. Retorna True se bem-sucedido."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao executar escrita: {e} | SQL: {sql}")
        return False
