from typing import Optional
from loguru import logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.repositories import knowledge_repo

embeddings: GoogleGenerativeAIEmbeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY,
)


def search_context(query: str) -> Optional[str]:
    """
    Gera embedding da query e busca chunks relevantes no Supabase pgvector.
    Retorna contexto concatenado ou None se sem resultado acima do threshold.
    """
    try:
        embedding: list = embeddings.embed_query(query)
        results: list = knowledge_repo.search_knowledge(embedding)

        if not results:
            return None

        context_parts = [chunk["content"] for chunk in results if chunk.get("content")]
        if not context_parts:
            return None

        return "\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"search_context error | query={query[:50]} | {e}")
        return None
