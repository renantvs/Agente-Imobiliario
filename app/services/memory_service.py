import json
from typing import List
from loguru import logger
from app.core.redis_client import redis_client
from app.core import postgres_client


def get_history(phone: str) -> List[dict]:
    """Retorna histórico de conversa do Redis (até 20 msgs). Retorna [] se vazio."""
    try:
        key = f"session:{phone}"
        raw = redis_client.get(key)
        if raw:
            return json.loads(raw)
        return []
    except Exception as e:
        logger.error(f"get_history error | phone={phone} | {e}")
        return []


def save_message(phone: str, role: str, content: str) -> None:
    """
    Salva mensagem no histórico Redis com TTL de 30 minutos.
    Mantém apenas as últimas 20 mensagens.
    """
    try:
        key = f"session:{phone}"
        history = get_history(phone)
        history.append({"role": role, "content": content})
        history = history[-20:]  # Manter só as últimas 20
        redis_client.setex(key, 1800, json.dumps(history))
    except Exception as e:
        logger.error(f"save_message error | phone={phone} | role={role} | {e}")


def persist_conversation(
    phone: str, user_msg: str, bot_response: str, intent: str
) -> None:
    """Persiste a troca de mensagens no PostgreSQL para memória de longo prazo."""
    try:
        postgres_client.execute_write(
            "INSERT INTO messages (phone, role, content, intent, created_at) "
            "VALUES (%s, %s, %s, %s, NOW())",
            (phone, "user", user_msg, intent),
        )
        postgres_client.execute_write(
            "INSERT INTO messages (phone, role, content, intent, created_at) "
            "VALUES (%s, %s, %s, %s, NOW())",
            (phone, "assistant", bot_response, intent),
        )
        logger.info(f"Conversa persistida no PostgreSQL | phone={phone}")
    except Exception as e:
        logger.error(f"persist_conversation error | phone={phone} | {e}")
