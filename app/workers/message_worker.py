import json
from datetime import timedelta
from typing import Optional

from loguru import logger
from rq import Queue
from rq.job import Job

from app.core.redis_client import redis_client
from app.core.config import settings
from app.models.schemas import IncomingMessage

queue: Queue = Queue("imob_agent", connection=redis_client)


def enqueue_message(msg: IncomingMessage) -> None:
    """
    Acumula mensagens do mesmo número por MESSAGE_BUFFER_SECONDS segundos.
    Cancela job anterior se nova mensagem chegar antes do timer.
    Agenda processamento unificado pelo worker.
    """
    buffer_key: str = f"buffer:{msg.phone}"
    job_key: str = f"job:{msg.phone}"
    buffer_ttl: int = settings.MESSAGE_BUFFER_SECONDS + 2

    try:
        # Carregar ou criar buffer
        existing_raw: Optional[str] = redis_client.get(buffer_key)
        if existing_raw:
            data: dict = json.loads(existing_raw)
            data["messages"].append(msg.message)
        else:
            data = {
                "phone": msg.phone,
                "phone_jid": msg.phone_jid,
                "name": msg.name or "",
                "messages": [msg.message],
            }

        redis_client.setex(buffer_key, buffer_ttl, json.dumps(data))

        # Cancelar job anterior se existir
        existing_job_id: Optional[str] = redis_client.get(job_key)
        if existing_job_id:
            try:
                old_job = Job.fetch(existing_job_id, connection=redis_client)
                old_job.cancel()
            except Exception:
                pass  # Job já executado ou expirado — ignorar

        # Agendar novo job com delay anti-flood
        new_job = queue.enqueue_in(
            timedelta(seconds=settings.MESSAGE_BUFFER_SECONDS),
            process_buffered_message,
            phone=msg.phone,
        )
        redis_client.setex(job_key, 30, new_job.id)

        logger.info(
            f"Mensagem enfileirada | {msg.phone} | "
            f"buffer acumulado: {len(data['messages'])} msg(s)"
        )

    except Exception as e:
        logger.error(f"enqueue_message error | phone={msg.phone} | {e}")


def process_buffered_message(phone: str) -> None:
    """
    Executado pelo worker RQ após o período de buffer.
    Concatena as mensagens acumuladas e invoca o agente LangGraph.
    """
    buffer_key: str = f"buffer:{phone}"

    try:
        raw: Optional[str] = redis_client.get(buffer_key)
        if not raw:
            logger.warning(f"Buffer vazio ou expirado | phone={phone}")
            return

        redis_client.delete(buffer_key)
        data: dict = json.loads(raw)
        messages: list = data.get("messages", [])
        name: str = data.get("name", "")

        if not messages:
            return

        full_message: str = " | ".join(messages)
        phone_jid: str = data.get("phone_jid", "")
        logger.info(
            f"Processando {len(messages)} mensagem(ns) acumulada(s) | phone={phone}"
        )

        # Import local para evitar import circular no módulo de workers
        from app.agents.graph import run_agent

        run_agent(phone=phone, phone_jid=phone_jid, message=full_message, name=name)

    except Exception as e:
        logger.error(f"process_buffered_message error | phone={phone} | {e}")
