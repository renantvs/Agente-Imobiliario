from loguru import logger
from app.services import rag_service


def search_rag(state: dict) -> dict:
    """
    Nó LangGraph: busca contexto relevante no Supabase via pgvector.
    Grava resultado em state['rag_context'] (str ou None).
    """
    try:
        context = rag_service.search_context(state["message"])
        state["rag_context"] = context

        if context:
            logger.info(f"RAG encontrou contexto | phone={state['phone']}")
        else:
            logger.info(f"RAG sem resultado relevante | phone={state['phone']}")
    except Exception as e:
        logger.error(f"search_rag error | phone={state['phone']} | {e}")
        state["rag_context"] = None

    return state
