from typing import Optional
import httpx
from loguru import logger
from app.core.config import settings


def send_message(phone_jid: str, text: str) -> bool:
    """
    Envia mensagem de texto via Evolution API.
    Faz até 2 tentativas em caso de falha.
    phone_jid deve conter o JID completo (ex: 5521920130578@s.whatsapp.net).
    """
    url = (
        f"{settings.EVOLUTION_API_URL}/message/sendText"
        f"/{settings.EVOLUTION_INSTANCE}"
    )
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"number": phone_jid, "text": text}

    for attempt in range(1, 3):
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201):
                    logger.info(f"Mensagem enviada | phone_jid={phone_jid} | tentativa={attempt}")
                    return True
                else:
                    logger.error(
                        f"Evolution API erro | status={response.status_code} "
                        f"| body={response.text} | url={url} | number={phone_jid}"
                    )
        except Exception as e:
            logger.warning(
                f"Erro ao enviar mensagem | phone_jid={phone_jid} | tentativa={attempt} | {e}"
            )

    logger.error(f"Falha definitiva ao enviar mensagem | phone_jid={phone_jid}")
    return False


def forward_to_human(from_phone: str, human_phone: str, context: str) -> None:
    """Encaminha alerta de escalação para o corretor humano via WhatsApp."""
    message = (
        f"📲 *Novo atendimento necessário*\n"
        f"Cliente: {from_phone}\n"
        f"Última mensagem: {context[:150]}"
    )
    try:
        send_message(human_phone, message)
        logger.info(
            f"Escalação encaminhada | from={from_phone} | human={human_phone}"
        )
    except Exception as e:
        logger.error(f"Erro ao encaminhar escalação | from={from_phone} | {e}")
