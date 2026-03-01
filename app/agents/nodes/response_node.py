from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from app.services.ai_service import llm_pro


def generate_response(state: dict) -> dict:
    """
    Nó LangGraph: gera resposta humanizada com Gemini Pro.
    Usa contexto RAG e histórico quando disponíveis.
    Grava resposta em state['response'].
    """
    fallback = "Desculpe, tive um problema técnico. Tente novamente! 😊"

    try:
        # Construir system prompt dinamicamente
        system_parts: List[str] = [
            "Você é Ana, corretora virtual da Imobiliária.",
            "Responda APENAS com informações do contexto fornecido.",
            "Se não souber, diga: 'Vou verificar isso pra você!'",
            "Máximo 3 frases curtas. Nunca invente dados. 🏠",
        ]

        if state.get("rag_context"):
            system_parts.append(
                f"\nBase de conhecimento:\n{state['rag_context']}"
            )

        history: list = state.get("history", [])
        if history:
            recent = history[-6:]
            history_text = "\n".join(
                f"{msg['role']}: {msg['content']}" for msg in recent
            )
            system_parts.append(f"\nHistórico recente:\n{history_text}")

        system_parts.append(f"Intenção identificada: {state.get('intent', 'unknown')}")

        system_prompt = "\n".join(system_parts)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["message"]),
        ]

        result = llm_pro.invoke(messages)
        state["response"] = result.content.strip()
        logger.info(f"Resposta gerada | phone={state['phone']}")

    except Exception as e:
        logger.error(f"generate_response error | phone={state['phone']} | {e}")
        state["response"] = fallback

    return state
