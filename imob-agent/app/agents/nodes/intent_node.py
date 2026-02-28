from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from app.services.ai_service import llm_flash
from app.models.schemas import Intent


def identify_intent(state: dict) -> dict:
    """
    Nó LangGraph: classifica a intenção da mensagem usando Gemini Flash.
    Resultado gravado em state['intent'].
    """
    valid_intents = {i.value for i in Intent}

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Classifique a intenção da mensagem em UMA dessas opções: "
            "faq, property_search, schedule_visit, lead_capture, escalation, "
            "greeting, unknown. "
            "Responda APENAS com a palavra, sem pontuação ou explicação.",
        ),
        ("human", "{message}"),
    ])

    try:
        chain = prompt | llm_flash
        result = chain.invoke({"message": state["message"]})
        intent_raw: str = result.content.strip().lower()

        if intent_raw in valid_intents:
            state["intent"] = intent_raw
        else:
            state["intent"] = Intent.unknown.value

        logger.info(
            f"Intenção identificada: {state['intent']} | phone={state['phone']}"
        )
    except Exception as e:
        logger.error(f"identify_intent error | phone={state['phone']} | {e}")
        state["intent"] = Intent.unknown.value

    return state
