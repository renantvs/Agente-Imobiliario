import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = "AIzaSyAO3ECjFU_hOmbolw64QILg8Lj5li4Q3E4"
    SUPABASE_URL: str = "https://romukfrgzzhnxntessft.supabase.co"
    SUPABASE_KEY: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvbXVrZnJnenpobnhudGVzc2Z0Iiwicm9sZSI6"
        "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjI0OTYxOSwiZXhwIjoyMDg3ODI1NjE5fQ."
        "QRbod-355xNCN2xZmAxsGd8uxgMwOScqZlxZag-XE0M"
    )
    POSTGRES_URL: str = (
        "postgresql://imobiliaria:cavaL02026"
        "@agente-imobilirio-postgresai-x6dyqc:5432/postgress_memory"
    )
    REDIS_URL: str = (
        "redis://default:cavaL02026@agente-imobilirio-redisdbai-2bfsnl:6379"
    )
    EVOLUTION_API_URL: str = "https://evoapi.imobiliaria.rptechconsultoria.com.br"
    EVOLUTION_API_KEY: str = (
        "1skkMS4R1hyxW0di96uzlkIeoQQ58IDcPNg21W1RnWlheQJcOAom3TFTRkywW4jf8wnPu7"
        "+GvjvQWfn3d8J3dQ=="
    )
    EVOLUTION_INSTANCE: str = "ED99C9FA3A19-4B60-B082-1C01AC26082C"
    HUMAN_PHONE: str = "552192013-0578"
    GMAIL_SENDER: str = ""
    LANGCHAIN_API_KEY: str = "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"
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "agentes-python-prod"
    MESSAGE_BUFFER_SECONDS: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.75
    APP_URL: str = "https://agente.imobiliaria.rptechconsultoria.com.br"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Propagar variáveis LangSmith para o ambiente de processo
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
