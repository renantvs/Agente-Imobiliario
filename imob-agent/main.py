import os

os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "agentes-python-prod")

from fastapi import FastAPI
from app.api.webhook import router
from loguru import logger

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


logger.info("Agente Imobiliário IA iniciado.")
