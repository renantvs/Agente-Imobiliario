import os

# Configurar LangSmith ANTES de qualquer import LangChain
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "agentes-python-prod"

from fastapi import FastAPI
from loguru import logger
from app.api.webhook import router

app = FastAPI(
    title="Agente Imobiliário IA",
    version="1.0.0",
    description="Agente de IA para WhatsApp — ramo imobiliário",
)

app.include_router(router)


@app.get("/health")
async def health():
    """Endpoint de health check para monitoramento do Dokploy."""
    return {
        "status": "ok",
        "service": "imob-agent",
        "version": "1.0.0",
        "url": "https://agente.imobiliaria.rptechconsultoria.com.br",
    }


logger.info("🏠 Agente Imobiliário IA iniciado com sucesso.")
