from loguru import logger
from app.services import escalation_service
from app.models.schemas import Intent

ESCALATION_TRIGGERS = [
    "falar com pessoa",
    "atendente",
    "humano",
    "gerente",
    "urgente",
    "reclamação",
    "corretor",
]


def check_escalation(state: dict) -> dict:
    """
    Nó LangGraph: detecta se a mensagem exige escalação para humano.
    Verifica triggers no texto e a intenção classificada.
    """
    message_lower = state["message"].lower()
    intent_is_escalation = state.get("intent") == Intent.escalation.value
    trigger_found = any(trigger in message_lower for trigger in ESCALATION_TRIGGERS)

    if intent_is_escalation or trigger_found:
        state["should_escalate"] = True
        logger.info(
            f"Escalação ativada | phone={state['phone']} "
            f"| intent={state.get('intent')} | trigger={trigger_found}"
        )
    else:
        state["should_escalate"] = False

    return state


def execute_escalation(state: dict) -> dict:
    """
    Nó LangGraph: executa a escalação — notifica humano e define resposta ao cliente.
    """
    try:
        escalation_service.trigger_escalation(
            phone=state["phone"],
            name=state.get("name", ""),
            last_message=state["message"],
        )
    except Exception as e:
        logger.error(f"execute_escalation error | phone={state['phone']} | {e}")

    state["response"] = (
        "Entendido! Vou te conectar com um de nossos corretores agora. Um momento! 🏠"
    )
    return state
