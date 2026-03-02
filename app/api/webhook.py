from fastapi import APIRouter, Request, HTTPException
from loguru import logger

from app.workers.message_worker import enqueue_message
from app.models.context import MessageContext

router = APIRouter()


# ---------------------------------------------------------------------------
# ZONA 1 — Entrada e normalização
# Responsabilidade exclusiva: extrair dados do payload Evolution API, montar
# o MessageContext e delegar para o worker. Zero lógica de negócio aqui.
# ---------------------------------------------------------------------------


def _build_context(body: dict) -> MessageContext | None:
    """
    Extrai e valida os campos relevantes do webhook Evolution API.
    Retorna MessageContext ou None se a mensagem deve ser ignorada.
    """
    if body.get("event") != "messages.upsert":
        return None

    data = body.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo bot
    if key.get("fromMe") is True:
        return None

    raw_jid: str = key.get("remoteJid", "")
    alt_jid: str = key.get("remoteJidAlt", "")

    # Ignorar grupos
    if raw_jid.endswith("@g.us"):
        return None

    # Resolver JID real (@lid = ID interno; número real está em remoteJidAlt)
    phone_jid = alt_jid if raw_jid.endswith("@lid") else raw_jid

    # Apenas dígitos → chave Redis / banco / logs
    phone = "".join(filter(str.isdigit, phone_jid.split("@")[0]))
    if not phone:
        return None

    # Extrair texto (conversação simples ou extendida)
    message_data = data.get("message", {})
    content: str = message_data.get("conversation") or (
        message_data.get("extendedTextMessage", {}).get("text", "")
    )
    if not content:
        return None

    return MessageContext(
        phone=phone,
        phone_jid=phone_jid,
        name=data.get("pushName", ""),
        content=content,
        message_id=key.get("id", ""),
    )


@router.post("/webhook/agente-imobiliaria")
async def webhook_agente(request: Request):
    """Endpoint principal do webhook (Evolution API)."""
    try:
        body = await request.json()
        ctx = _build_context(body)
        if ctx is None:
            return {"status": "ignored"}
        logger.info(f"Webhook recebido | phone={ctx.phone} | msg={ctx.content[:50]}")
        enqueue_message(ctx)
        return {"status": "queued"}
    except Exception as e:
        logger.error(f"webhook_agente error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no webhook")


@router.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    """Endpoint alternativo — compatibilidade com Evolution API v2."""
    try:
        body = await request.json()
        ctx = _build_context(body)
        if ctx is None:
            return {"status": "ignored"}
        logger.info(f"Webhook evolution | phone={ctx.phone} | msg={ctx.content[:50]}")
        enqueue_message(ctx)
        return {"status": "queued"}
    except Exception as e:
        logger.error(f"webhook_evolution error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no webhook")
