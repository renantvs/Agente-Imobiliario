from loguru import logger
from app.services import whatsapp_service
from app.core.config import settings


def trigger_escalation(phone: str, name: str, last_message: str) -> None:
    """
    Dispara escalação: notifica corretor humano e loga o evento.
    """
    try:
        whatsapp_service.forward_to_human(
            from_phone=phone,
            human_phone=settings.HUMAN_PHONE,
            context=last_message,
        )
        logger.info(
            f"Escalação disparada | phone={phone} | name={name or 'desconhecido'}"
        )
    except Exception as e:
        logger.error(f"trigger_escalation error | phone={phone} | {e}")
