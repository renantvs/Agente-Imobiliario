import uuid
from typing import Optional
from loguru import logger
from app.core import postgres_client


def get_or_create_conversation(phone: str) -> dict:
    """
    Retorna conversa ativa existente ou cria uma nova.
    Retorna dict com campos da conversa ou {} em caso de erro.
    """
    try:
        rows = postgres_client.execute_query(
            "SELECT id, phone, status, created_at FROM conversations "
            "WHERE phone = %s AND status = 'active' LIMIT 1",
            (phone,),
        )
        if rows:
            return rows[0]

        new_id = str(uuid.uuid4())
        success = postgres_client.execute_write(
            "INSERT INTO conversations (id, phone, status, created_at) "
            "VALUES (%s, %s, 'active', NOW())",
            (new_id, phone),
        )
        if success:
            logger.info(f"Nova conversa criada | phone={phone} | id={new_id}")
            return {"id": new_id, "phone": phone, "status": "active"}

        logger.error(f"Falha ao criar conversa para phone={phone}")
        return {}
    except Exception as e:
        logger.error(f"get_or_create_conversation error | phone={phone} | {e}")
        return {}


def update_conversation_status(phone: str, status: str) -> bool:
    """Atualiza o status de conversa ativa para o phone informado."""
    try:
        return postgres_client.execute_write(
            "UPDATE conversations SET status = %s WHERE phone = %s AND status = 'active'",
            (status, phone),
        )
    except Exception as e:
        logger.error(f"update_conversation_status error | phone={phone} | {e}")
        return False
