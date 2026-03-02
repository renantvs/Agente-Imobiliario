"""
ZONA 5 — Agente de Qualificação de Lead

Responsabilidade: coletar perfil do comprador/locatário de forma progressiva e natural.
Redis: {phone}_qualificacao | TTL: 900s | Janela: 20 mensagens
"""

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.services.ai_service import llm_flash
from app.services.memory_service import get_agent_history, save_agent_message

AGENT_NAME = "qualificacao"
AGENT_TTL = 900
MAX_HISTORY = 20

_SYSTEM_PROMPT = (
    "Você é Ana, corretora virtual especializada em entender o que o cliente busca.\n\n"
    "Seu objetivo: qualificar o lead de forma progressiva e natural, coletando informações\n"
    "sem parecer um formulário. Uma pergunta de cada vez.\n\n"
    "Informações a coletar (em ordem natural de conversa):\n"
    "- Tipo de imóvel (apartamento, casa, comercial)\n"
    "- Finalidade (compra ou aluguel)\n"
    "- Bairro ou região de interesse\n"
    "- Número de quartos / área aproximada\n"
    "- Faixa de valor disponível\n\n"
    "Diretrizes:\n"
    "- Máximo 1 pergunta por mensagem\n"
    "- Reconheça o que o usuário disse antes de perguntar o próximo item\n"
    "- Mostre genuíno interesse — você realmente quer ajudar a encontrar o imóvel certo\n"
    "- Formato valores: R$ 1.500,00\n"
    "- Negrito WhatsApp: *texto* (nunca **duplo**)\n"
    "- Sem markdown (proibido ###, ---, tabelas)\n\n"
    "Exemplo de abertura:\n"
    "'Pra eu te indicar as melhores opções, me conta um pouco mais sobre o que você está "
    "buscando? Pode ser bem à vontade! 😊'"
)


def qualification_agent(state: dict) -> dict:
    """Zona 5 — Agente de qualificação de lead."""
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
        logger.info(f"Agente qualificação respondeu | phone={phone}")

    except Exception as e:
        logger.error(f"qualification_agent error | phone={phone} | {e}")
        state["response"] = (
            "Pra eu te indicar as melhores opções, me conta um pouco mais "
            "sobre o que você está buscando? Pode ser à vontade! 😊"
        )

    return state
