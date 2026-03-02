"""
ZONA 3 — Classificação de intenção com cache de sessão Redis

Fluxo:
1. Verificar chave intent:{phone} no Redis — reusar se existir
2. Classificar com gpt-4o-mini, saída JSON estruturada
3. Salvar em intent:{phone} com TTL 60s
4. Popular state["intent"] e state["classified_intent"]
"""

import json

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.services.ai_service import llm_flash
from app.models.schemas import Intent, ClassifiedIntent
from app.core.redis_client import redis_client

INTENT_CACHE_TTL = 60  # segundos

_SYSTEM_PROMPT = (
    "Você é um classificador de intenções para um assistente imobiliário.\n"
    "Classifique a mensagem do usuário em UMA das intenções abaixo:\n\n"
    "  agendamento      → querer visitar imóvel, marcar horário, agendar visita\n"
    "  qualificacao     → perguntas sobre imóveis, busca, preço, localização, financiamento\n"
    "  documentacao     → envio ou dúvidas sobre documentos, contrato, escritura\n"
    "  atendimento_humano → pedir corretor, falar com pessoa, urgente, reclamação\n"
    "  cumprimento      → oi, olá, bom dia, tudo bem, boa tarde, início de conversa\n"
    "  indefinido       → não se enquadra em nenhuma das anteriores\n\n"
    "Responda APENAS com JSON válido neste formato, sem markdown:\n"
    '{"intencao": "<valor>", "confianca": "<alta|media|baixa>", "entidades": {}}'
)

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "{message}"),
])

_valid_intents = {i.value for i in Intent}


def identify_intent(state: dict) -> dict:
    """
    Zona 3 — Nó LangGraph de classificação de intenção.
    Verifica cache Redis antes de chamar o LLM.
    """
    phone = state["phone"]
    cache_key = f"intent:{phone}"

    # 1. Tentar cache Redis
    cached = redis_client.get(cache_key)
    if cached:
        try:
            data: ClassifiedIntent = json.loads(cached)
            state["intent"] = data["intencao"]
            state["classified_intent"] = data
            logger.info(f"Intenção do cache Redis | {phone} | {data['intencao']}")
            return state
        except Exception:
            pass  # Cache corrompido — classificar normalmente

    # 2. Classificar com LLM
    try:
        chain = _prompt | llm_flash
        result = chain.invoke({"message": state["message"]})
        raw = result.content.strip()

        # Limpar markdown se houver (```json ... ```)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data: ClassifiedIntent = json.loads(raw)
        intencao = data.get("intencao", "indefinido")

        # Garantir que a intenção é válida
        if intencao not in _valid_intents:
            intencao = Intent.indefinido.value
        data["intencao"] = intencao

        # 3. Salvar no cache Redis com TTL 60s
        redis_client.setex(cache_key, INTENT_CACHE_TTL, json.dumps(data))

        state["intent"] = intencao
        state["classified_intent"] = data
        logger.info(
            f"Intenção classificada | phone={phone} | {intencao} "
            f"| confianca={data.get('confianca')}"
        )

    except Exception as e:
        logger.error(f"identify_intent error | phone={phone} | {e}")
        fallback: ClassifiedIntent = {
            "intencao": Intent.indefinido.value,
            "confianca": "baixa",
            "entidades": {},
        }
        state["intent"] = Intent.indefinido.value
        state["classified_intent"] = fallback

    return state
