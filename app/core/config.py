import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # POSTGRES_URL deve usar porta 5432 (Supabase PostgreSQL), NÃO 6380 (que é porta do Redis)
    # Exemplo correto: postgresql://user:pass@host:5432/postgres
    POSTGRES_URL: str = ""
    REDIS_URL: str = ""
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = ""
    HUMAN_PHONE: str = "552192013-0578"
    GMAIL_SENDER: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_PROJECT: str = "agentes-python-prod"
    MESSAGE_BUFFER_SECONDS: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.75
    APP_URL: str = "https://agente.imobiliaria.rptechconsultoria.com.br"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Garantir que o SDK do LangSmith respeite a configuração de tracing.
# Sem isso, o SDK pode tentar autenticar mesmo com LANGCHAIN_TRACING_V2=false.
if settings.LANGCHAIN_TRACING_V2.lower() != "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
