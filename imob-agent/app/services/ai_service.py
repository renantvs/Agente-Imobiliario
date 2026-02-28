from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

llm_pro: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1,
)

llm_flash: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.0,
)

__all__ = ["llm_pro", "llm_flash"]
