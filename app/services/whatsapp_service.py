from typing import Optional
import httpx
from loguru import logger
from app.core.config import settings


def send_message(phone: str, text: str) -> bool:
    """
    Envia mensagem de texto via Evolution API.
    Faz até 2 tentativas em caso de falha.
    """
    url = (
        f"{settings.EVOLUTION_API_URL}/message/sendText"
        f"/{settings.EVOLUTION_INSTANCE}"
    )
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"number": phone, "text": text}

    for attempt in range(1, 3):
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Mensagem enviada | phone={phone} | tentativa={attempt}")
                return True
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"HTTP error ao enviar mensagem | phone={phone} "
                f"| status={e.response.status_code} | tentativa={attempt}"
            )
        except Exception as e:
            logger.warning(
                f"Erro ao enviar mensagem | phone={phone} | tentativa={attempt} | {e}"
            )

    logger.error(f"Falha definitiva ao enviar mensagem | phone={phone}")
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
