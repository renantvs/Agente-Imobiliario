from typing import Optional
from loguru import logger
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.repositories import knowledge_repo

# TEMPORARIAMENTE DESABILITADO: text-embedding-3-small gera vetores de 1536 dimensões,
# mas o schema do Supabase está configurado com vector(768) (Gemini text-embedding-004).
# O search_context retorna sempre None até que o schema seja migrado para vector(1536).
# Para reativar: remova o bloco de retorno antecipado e recrie a coluna no Supabase.

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.OPENAI_API_KEY,
)


def search_context(query: str) -> Optional[str]:
    """
    Gera embedding da query e busca chunks relevantes no Supabase pgvector.
    Retorna contexto concatenado ou None se sem resultado acima do threshold.
    """
    # TODO: reativar após migrar Supabase para vector(1536)
    return None

    try:  # noqa: unreachable — mantido para facilitar reativação futura
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
