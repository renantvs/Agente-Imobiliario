import json
import threading

from loguru import logger
from redis import Redis

from app.core.config import settings
from app.models.schemas import IncomingMessage

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Dicionário para controlar timers ativos por número
_timers: dict[str, threading.Timer] = {}
_timers_lock = threading.Lock()


def enqueue_message(msg: IncomingMessage) -> None:
    """
    Acumula mensagens do mesmo número por MESSAGE_BUFFER_SECONDS segundos usando
    threading.Timer — sem dependência de RQ Scheduler externo.
    Cancela e recria o timer a cada nova mensagem recebida (anti-flood).
    """
    buffer_key = f"buffer:{msg.phone}"

    # Carregar buffer existente ou criar novo
    existing = redis_client.get(buffer_key)
    if existing:
        data = json.loads(existing)
        data["messages"].append(msg.message)
    else:
        data = {
            "phone": msg.phone,
            "phone_jid": msg.phone_jid,
            "name": msg.name or "",
            "messages": [msg.message],
        }

    # Salvar buffer atualizado com TTL de segurança
    redis_client.setex(
        buffer_key,
        settings.MESSAGE_BUFFER_SECONDS + 5,
        json.dumps(data),
    )

    # Cancelar timer anterior e criar novo
    with _timers_lock:
        if msg.phone in _timers:
            _timers[msg.phone].cancel()
            logger.info(f"Timer anterior cancelado | {msg.phone}")

        timer = threading.Timer(
            settings.MESSAGE_BUFFER_SECONDS,
            process_buffered_message,
            args=[msg.phone],
        )
        timer.daemon = True
        timer.start()
        _timers[msg.phone] = timer

    logger.info(
        f"Mensagem enfileirada | {msg.phone} | "
        f"buffer acumulado: {len(data['messages'])} msg(s)"
    )


def process_buffered_message(phone: str) -> None:
    """
    Chamado pelo threading.Timer após o período de buffer.
    Concatena as mensagens acumuladas e invoca o agente LangGraph.
    """
    logger.info(f"Worker processando mensagem | phone={phone}")
    buffer_key = f"buffer:{phone}"

    # Buscar e deletar buffer atomicamente
    raw = redis_client.get(buffer_key)
    if not raw:
        logger.warning(f"Buffer vazio ou expirado | {phone}")
        return

    redis_client.delete(buffer_key)

    # Remover timer do dicionário
    with _timers_lock:
        _timers.pop(phone, None)

    data = json.loads(raw)
    messages: list = data.get("messages", [])
    if not messages:
        return

    full_message = " | ".join(messages)
    phone_jid: str = data.get("phone_jid", "")

    logger.info(
        f"Processando {len(messages)} mensagem(ns) acumulada(s) | "
        f"phone={phone} | '{full_message[:50]}'"
    )

    try:
        from app.agents.graph import run_agent

        run_agent(
            phone=data["phone"],
            phone_jid=phone_jid,
            message=full_message,
            name=data.get("name", ""),
        )
    except Exception as e:
        logger.error(f"Erro ao processar mensagem | phone={phone} | {e}")
