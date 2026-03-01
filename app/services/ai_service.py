from langchain_openai import ChatOpenAI
from app.core.config import settings

llm_pro: ChatOpenAI = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=settings.OPENAI_API_KEY,
    temperature=0.1,
)

llm_flash: ChatOpenAI = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=settings.OPENAI_API_KEY,
    temperature=0.0,
)

__all__ = ["llm_pro", "llm_flash"]
