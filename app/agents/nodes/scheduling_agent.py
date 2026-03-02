"""
ZONA 5 — Agente de Agendamento

Responsabilidade: coletar dia/horário e confirmar visita ao imóvel.
Redis: {phone}_agendamento | TTL: 600s | Janela: 15 mensagens
"""

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.services.ai_service import llm_flash
from app.services.memory_service import get_agent_history, save_agent_message

AGENT_NAME = "agendamento"
AGENT_TTL = 600
MAX_HISTORY = 15

_SYSTEM_PROMPT = (
    "Você é Ana, corretora virtual especializada em agendamento de visitas.\n\n"
    "Seu objetivo: ajudar o usuário a marcar uma visita a um imóvel de forma natural e amigável.\n\n"
    "Diretrizes:\n"
    "- Pergunte qual imóvel o usuário tem interesse (se não souber)\n"
    "- Descubra qual dia e horário funcionam melhor\n"
    "- Confirme o agendamento de forma calorosa\n"
    "- Máximo 3 frases por mensagem\n"
    "- Tom: próximo, atencioso e eficiente — como um corretor de confiança\n"
    "- Nunca invente horários ou disponibilidades\n"
    "- Formato de datas: dd/MM/yyyy\n"
    "- Negrito WhatsApp: *texto* (nunca **duplo**)\n"
    "- Sem markdown (proibido ###, ---, tabelas)\n\n"
    "Exemplo de abertura:\n"
    "'Que ótimo que você quer conhecer o imóvel pessoalmente! 🏠 "
    "Vamos encontrar um horário que funcione pra você. Qual dia da semana costuma ser melhor?'"
)


def scheduling_agent(state: dict) -> dict:
    """Zona 5 — Agente de agendamento de visitas."""
    phone = state["phone"]
    name = state.get("name", "")

    try:
        history = get_agent_history(phone, AGENT_NAME, MAX_HISTORY)
        name_hint = f"Nome do usuário: {name}\n" if name else ""

        messages = [
            SystemMessage(content=name_hint + _SYSTEM_PROMPT),
            *[
                (HumanMessage if m["role"] == "user" else SystemMessage)(content=m["content"])
                for m in history
            ],
            HumanMessage(content=state["message"]),
        ]

        result = llm_flash.invoke(messages)
        response = result.content.strip()

        save_agent_message(phone, AGENT_NAME, "user", state["message"], AGENT_TTL)
        save_agent_message(phone, AGENT_NAME, "assistant", response, AGENT_TTL)

        state["response"] = response
        logger.info(f"Agente agendamento respondeu | phone={phone}")

    except Exception as e:
        logger.error(f"scheduling_agent error | phone={phone} | {e}")
        state["response"] = (
            "Que ótimo que você quer conhecer o imóvel! 🏠 "
            "Qual dia da semana costuma ser melhor pra você?"
        )

    return state
