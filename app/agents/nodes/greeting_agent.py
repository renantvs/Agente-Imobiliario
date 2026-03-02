"""
ZONA 5 — Agente Inicializador (cumprimento)

Responsabilidade: receber o usuário com acolhimento e direcionar para o próximo passo.
Redis: {phone}_cumprimento | TTL: 180s | Janela: 5 mensagens
"""

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.services.ai_service import llm_flash
from app.services.memory_service import get_agent_history, save_agent_message

AGENT_NAME = "cumprimento"
AGENT_TTL = 180
MAX_HISTORY = 5

_SYSTEM_PROMPT = (
    "Você é Ana, corretora virtual de uma imobiliária.\n"
    "Seu objetivo agora é receber o usuário com calor e descobrir como pode ajudá-lo.\n\n"
    "Diretrizes:\n"
    "- Use o nome do usuário se disponível\n"
    "- Seja calorosa, próxima e natural — nunca robótica\n"
    "- Apresente-se brevemente e pergunte o que o usuário está procurando\n"
    "- Máximo 3 frases curtas\n"
    "- Nunca use linguagem de sistema (ex: 'operação realizada', 'dado registrado')\n"
    "- Emojis com moderação e naturalidade\n"
    "- Negrito WhatsApp: *texto* (nunca **duplo**)\n\n"
    "Exemplo de abertura:\n"
    "'Oi, [nome]! Tudo bem? 😊 Sou a Ana, corretora virtual da nossa imobiliária "
    "— estou aqui pra te ajudar a encontrar o imóvel ideal. O que você está procurando?'"
)


def greeting_agent(state: dict) -> dict:
    """Zona 5 — Agente de cumprimento e abertura de atendimento."""
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
        logger.info(f"Agente cumprimento respondeu | phone={phone}")

    except Exception as e:
        logger.error(f"greeting_agent error | phone={phone} | {e}")
        state["response"] = (
            f"Oi{', ' + name if name else ''}! 😊 Tudo bem? Sou a Ana, corretora virtual. "
            "Como posso te ajudar hoje?"
        )

    return state
