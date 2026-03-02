"""
ZONA 5 — Agente de mensagem não compreendida (indefinido)

Responsabilidade: responder com empatia quando a intenção não foi identificada.
Não usa LLM — resposta estática humanizada para não gerar latência desnecessária.
"""

from loguru import logger


def unknown_agent(state: dict) -> dict:
    """Zona 5 — Agente para intenções indefinidas."""
    phone = state["phone"]
    name = state.get("name", "")

    name_txt = f", {name.split()[0]}" if name else ""
    state["response"] = (
        f"Hmm, não entendi muito bem o que você quis dizer{name_txt}. 😅 "
        "Pode me contar de outra forma? Estou aqui pra ajudar!"
    )

    logger.info(f"Agente indefinido respondeu | phone={phone}")
    return state
