import uuid
from typing import List, Optional
from loguru import logger
from app.core.supabase_client import supabase
from app.core.config import settings


def search_knowledge(
    embedding: List[float],
    threshold: Optional[float] = None,
    count: int = 3,
) -> List[dict]:
    """
    Busca chunks de conhecimento no Supabase via pgvector.
    Retorna lista de dicts com id, content, category, similarity.
    """
    try:
        match_threshold = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD
        response = supabase.rpc(
            "match_knowledge",
            {
                "query_embedding": embedding,
                "match_threshold": match_threshold,
                "match_count": count,
            },
        ).execute()
        if response.data:
            return [
                {
                    "id": row.get("id"),
                    "content": row.get("content"),
                    "category": row.get("category"),
                    "similarity": row.get("similarity"),
                }
                for row in response.data
            ]
        return []
    except Exception as e:
        logger.error(f"search_knowledge error: {e}")
        return []


def insert_knowledge(
    content: str,
    embedding: List[float],
    category: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """Insere um novo chunk de conhecimento na tabela knowledge_base."""
    try:
        payload = {
            "id": str(uuid.uuid4()),
            "content": content,
            "embedding": embedding,
            "category": category,
            "metadata": metadata or {},
        }
        supabase.table("knowledge_base").insert(payload).execute()
        logger.info(f"Conhecimento inserido | category={category}")
        return True
    except Exception as e:
        logger.error(f"insert_knowledge error: {e}")
        return False
