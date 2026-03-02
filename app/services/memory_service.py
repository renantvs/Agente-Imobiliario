"""
Serviço de memória de sessão.

Memória em 2 camadas:
- Redis  → rápida, TTL por agente, histórico de contexto imediato
- PostgreSQL → persistente, histórico de longo prazo por número

Funções por agente usam chaves isoladas no formato {phone}_{agent_name}.
Funções genéricas (get_history / save_message) mantidas para compatibilidade.
"""

import json
from typing import List
from loguru import logger

from app.core.redis_client import redis_client
from app.core import postgres_client


# ---------------------------------------------------------------------------
# Memória por agente — chave isolada {phone}_{agent_name}
# ---------------------------------------------------------------------------

def get_agent_history(phone: str, agent_name: str, max_msgs: int = 10) -> List[dict]:
    """
    Retorna o histórico de um agente específico do Redis.
    Chave: {phone}_{agent_name} | Retorna [] se vazio ou expirado.
    """
    try:
        key = f"{phone}_{agent_name}"
        raw = redis_client.get(key)
        if raw:
            history = json.loads(raw)
            return history[-max_msgs:]
        return []
    except Exception as e:
        logger.error(f"get_agent_history error | phone={phone} | agent={agent_name} | {e}")
        return []


def save_agent_message(
    phone: str,
    agent_name: str,
    role: str,
    content: str,
    ttl: int,
) -> None:
    """
    Salva mensagem na memória isolada de um agente com TTL específico.
    Chave: {phone}_{agent_name}
    """
    try:
        key = f"{phone}_{agent_name}"
        history = get_agent_history(phone, agent_name, max_msgs=100)
        history.append({"role": role, "content": content})
        redis_client.setex(key, ttl, json.dumps(history))
    except Exception as e:
        logger.error(
            f"save_agent_message error | phone={phone} | agent={agent_name} | {e}"
        )


# ---------------------------------------------------------------------------
# Memória genérica de sessão — chave session:{phone}
# Mantida para compatibilidade com o fluxo geral
# ---------------------------------------------------------------------------

def get_history(phone: str) -> List[dict]:
    """Retorna histórico genérico de sessão do Redis (até 20 msgs)."""
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
    Salva mensagem no histórico genérico Redis com TTL de 30 minutos.
    Mantém apenas as últimas 20 mensagens.
    """
    try:
        key = f"session:{phone}"
        history = get_history(phone)
        history.append({"role": role, "content": content})
        history = history[-20:]
        redis_client.setex(key, 1800, json.dumps(history))
    except Exception as e:
        logger.error(f"save_message error | phone={phone} | role={role} | {e}")


# ---------------------------------------------------------------------------
# Persistência de longo prazo — PostgreSQL
# ---------------------------------------------------------------------------

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
