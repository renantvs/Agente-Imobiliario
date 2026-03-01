from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    POSTGRES_URL: str = ""
    REDIS_URL: str = ""
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = ""
    HUMAN_PHONE: str = "552192013-0578"
    GMAIL_SENDER: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "agentes-python-prod"
    MESSAGE_BUFFER_SECONDS: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.75
    APP_URL: str = "https://agente.imobiliaria.rptechconsultoria.com.br"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
