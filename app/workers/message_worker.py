"""
ZONA 2 — Buffer e normalização de mensagens

Padrão RPUSH + deduplicação por message_id:
1. RPUSH buffer:{phone} <json> com TTL de segurança
2. threading.Timer como mecanismo de delay (sem dependência de RQ Scheduler)
3. Ao disparar: compara message_id atual com o da última mensagem na lista
4. Se igual  → consolida todas as mensagens e processa
5. Se diferente → encerra silenciosamente (outra invocação vai processar)
6. DEL buffer:{phone} após processamento
"""

import json
import threading

from loguru import logger
from redis import Redis

from app.core.config import settings
from app.models.context import MessageContext

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Controle de timers ativos por número
_timers: dict[str, threading.Timer] = {}
_timers_lock = threading.Lock()


def enqueue_message(ctx: MessageContext) -> None:
    """
    Zona 2 — Entrada do buffer.
    Registra a mensagem na lista Redis e agenda o processamento com debounce.
    """
    buffer_key = f"buffer:{ctx.phone}"
    ttl = settings.MESSAGE_BUFFER_SECONDS + 5

    # Append na lista Redis — preserva ordem de chegada
    payload = json.dumps({
        "phone": ctx.phone,
        "phone_jid": ctx.phone_jid,
        "name": ctx.name,
        "content": ctx.content,
        "message_id": ctx.message_id,
    })
    redis_client.rpush(buffer_key, payload)
    redis_client.expire(buffer_key, ttl)

    # Cancelar timer anterior e registrar o novo (debounce)
    with _timers_lock:
        if ctx.phone in _timers:
            _timers[ctx.phone].cancel()
            logger.debug(f"Timer anterior cancelado | {ctx.phone}")

        timer = threading.Timer(
            settings.MESSAGE_BUFFER_SECONDS,
            _process_buffer,
            kwargs={"phone": ctx.phone, "trigger_message_id": ctx.message_id},
        )
        timer.daemon = True
        timer.start()
        _timers[ctx.phone] = timer

    logger.info(
        f"Mensagem enfileirada | {ctx.phone} | "
        f"buffer: {redis_client.llen(buffer_key)} msg(s)"
    )


def _process_buffer(phone: str, trigger_message_id: str) -> None:
    """
    Zona 2 — Processamento do buffer após o delay.
    Deduplica pelo message_id da última mensagem na lista.
    Consolida e chama o agente apenas se esta invocação é a mais recente.
    """
    logger.info(f"Worker processando mensagem | phone={phone}")
    buffer_key = f"buffer:{phone}"

    # Ler última mensagem sem deletar (peek)
    raw_items = redis_client.lrange(buffer_key, 0, -1)
    if not raw_items:
        logger.warning(f"Buffer vazio ou expirado | phone={phone}")
        return

    last_item = json.loads(raw_items[-1])
    last_message_id = last_item.get("message_id", "")

    # Deduplicação: só processa se este timer foi disparado pela última mensagem
    if trigger_message_id and last_message_id and trigger_message_id != last_message_id:
        logger.debug(
            f"Invocação ignorada (não é a mais recente) | phone={phone} "
            f"| trigger={trigger_message_id[:8]} | last={last_message_id[:8]}"
        )
        return

    # Consumir e deletar buffer atomicamente
    raw_items = redis_client.lrange(buffer_key, 0, -1)
    redis_client.delete(buffer_key)

    # Limpar referência do timer
    with _timers_lock:
        _timers.pop(phone, None)

    # Consolidar mensagens em ordem de chegada
    items = [json.loads(r) for r in raw_items]
    if not items:
        return

    first = items[0]
    consolidated_content = " | ".join(i["content"] for i in items)

    logger.info(
        f"Processando {len(items)} mensagem(ns) | phone={phone} "
        f"| '{consolidated_content[:60]}'"
    )

    try:
        from app.agents.graph import run_agent

        run_agent(
            phone=first["phone"],
            phone_jid=first["phone_jid"],
            name=first.get("name", ""),
            message=consolidated_content,
            message_id=trigger_message_id,
        )
    except Exception as e:
        logger.error(f"Erro ao processar buffer | phone={phone} | {e}")
