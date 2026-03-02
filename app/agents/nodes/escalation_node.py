"""
ZONA 5 — Agente de Escalação para Atendimento Humano

Responsabilidade: detectar pedido de humano, notificar corretor e responder ao cliente.
Mantém lógica existente com linguagem humanizada.
"""

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
    Zona 5 — Detecta se a mensagem exige escalação para humano.
    Verifica triggers no texto e a intenção classificada.
    """
    message_lower = state["message"].lower()
    intent_is_escalation = state.get("intent") == Intent.atendimento_humano.value
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
    Zona 5 — Executa a escalação: notifica corretor humano e define resposta ao cliente.
    """
    try:
        escalation_service.trigger_escalation(
            phone=state["phone"],
            name=state.get("name", ""),
            last_message=state["message"],
        )
    except Exception as e:
        logger.error(f"execute_escalation error | phone={state['phone']} | {e}")

    name = state.get("name", "")
    name_txt = f", {name.split()[0]}" if name else ""
    state["response"] = (
        f"Claro{name_txt}! Vou chamar um dos nossos corretores agora. 🙏 "
        "Em breve alguém da equipe vai entrar em contato com você. Obrigada pela paciência!"
    )
    return state
