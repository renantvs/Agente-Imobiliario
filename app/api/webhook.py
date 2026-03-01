from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from app.workers.message_worker import enqueue_message
from app.models.schemas import IncomingMessage

router = APIRouter()


def _extract_message_from_body(body: dict):
    """
    Extrai e valida os campos relevantes do webhook da Evolution API.
    Retorna IncomingMessage ou None se a mensagem deve ser ignorada.
    """
    # Ignorar eventos que não sejam novas mensagens
    if body.get("event") != "messages.upsert":
        return None

    data = body.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo próprio bot
    if key.get("fromMe") is True:
        return None

    remote_jid: str = key.get("remoteJid", "")

    # Ignorar mensagens de grupos
    if remote_jid.endswith("@g.us"):
        return None

    # Normalizar número de telefone
    phone = remote_jid.replace("@s.whatsapp.net", "")
    if not phone:
        return None

    # Extrair texto (mensagem simples ou texto extendido)
    message_data = data.get("message", {})
    text: str = message_data.get("conversation") or (
        message_data.get("extendedTextMessage", {}).get("text", "")
    )
    if not text:
        return None

    name: str = data.get("pushName", "")

    return IncomingMessage(phone=phone, message=text, name=name)


@router.post("/webhook/agente-imobiliaria")
async def webhook_agente(request: Request):
    """Endpoint principal do webhook (Evolution API configurado no Dokploy)."""
    try:
        body = await request.json()
        msg = _extract_message_from_body(body)

        if msg is None:
            return {"status": "ignored"}

        logger.info(f"Webhook recebido | phone={msg.phone} | msg={msg.message[:50]}")
        enqueue_message(msg)
        return {"status": "queued"}

    except Exception as e:
        logger.error(f"webhook_agente error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no webhook")


@router.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    """Endpoint alternativo para compatibilidade com Evolution API v2."""
    try:
        body = await request.json()
        msg = _extract_message_from_body(body)

        if msg is None:
            return {"status": "ignored"}

        logger.info(f"Webhook evolution | phone={msg.phone} | msg={msg.message[:50]}")
        enqueue_message(msg)
        return {"status": "queued"}

    except Exception as e:
        logger.error(f"webhook_evolution error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no webhook")
