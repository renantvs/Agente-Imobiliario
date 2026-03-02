"""
ZONA 5 — Agente de Documentação

Responsabilidade: receber documentos e responder dúvidas sobre documentação.
Redis: {phone}_documentacao | TTL: 600s | Janela: 10 mensagens
"""

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.services.ai_service import llm_flash
from app.services.memory_service import get_agent_history, save_agent_message

AGENT_NAME = "documentacao"
AGENT_TTL = 600
MAX_HISTORY = 10

_SYSTEM_PROMPT = (
    "Você é Ana, corretora virtual especializada em orientar sobre documentação imobiliária.\n\n"
    "Seu objetivo: ajudar o usuário com dúvidas sobre documentos, contratos e processos.\n\n"
    "Diretrizes:\n"
    "- Seja clara e acolhedora — documentação pode ser intimidadora\n"
    "- Confirme recebimento de documentos com naturalidade\n"
    "- Oriente sobre próximos passos de forma simples\n"
    "- Se um documento foi enviado, confirme e informe o que vem a seguir\n"
    "- Nunca invente informações jurídicas ou prazos sem certeza\n"
    "- Máximo 3 frases por mensagem\n"
    "- Negrito WhatsApp: *texto* (nunca **duplo**)\n"
    "- Sem markdown (proibido ###, ---, tabelas)\n\n"
    "Exemplo ao receber documento:\n"
    "'Recebi seu documento! 📄 Deixa eu dar uma olhadinha aqui... "
    "Pode enviar os próximos quando quiser, estou por aqui.'"
)


def documentation_agent(state: dict) -> dict:
    """Zona 5 — Agente de documentação."""
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
        logger.info(f"Agente documentação respondeu | phone={phone}")

    except Exception as e:
        logger.error(f"documentation_agent error | phone={phone} | {e}")
        state["response"] = (
            "Recebi sua mensagem! 📄 Se quiser enviar algum documento, "
            "pode mandar aqui mesmo — estou por aqui para ajudar."
        )

    return state
