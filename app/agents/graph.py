from loguru import logger
from langgraph.graph import StateGraph, END

from app.agents.nodes.intent_node import identify_intent
from app.agents.nodes.rag_node import search_rag
from app.agents.nodes.response_node import generate_response
from app.agents.nodes.escalation_node import check_escalation, execute_escalation
from app.services import memory_service, whatsapp_service
from app.models.schemas import AgentState


def route_after_intent(state: dict) -> str:
    """Roteamento após classificação de intenção."""
    intents_needing_rag = {"faq", "property_search", "unknown"}
    if state.get("intent") in intents_needing_rag:
        return "rag"
    return "check_escalation"


def route_after_check(state: dict) -> str:
    """Roteamento após verificação de escalação."""
    if state.get("should_escalate"):
        return "escalate"
    return "respond"


def _build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph a cada execução."""
    graph = StateGraph(dict)

    graph.add_node("intent", identify_intent)
    graph.add_node("rag", search_rag)
    graph.add_node("check_escalation", check_escalation)
    graph.add_node("escalate", execute_escalation)
    graph.add_node("respond", generate_response)

    graph.set_entry_point("intent")

    graph.add_conditional_edges(
        "intent",
        route_after_intent,
        {"rag": "rag", "check_escalation": "check_escalation"},
    )
    graph.add_edge("rag", "check_escalation")
    graph.add_conditional_edges(
        "check_escalation",
        route_after_check,
        {"escalate": "escalate", "respond": "respond"},
    )
    graph.add_edge("escalate", END)
    graph.add_edge("respond", END)

    return graph.compile()


def run_agent(phone: str, message: str, name: str = "", phone_jid: str = "") -> None:
    """
    Ponto de entrada principal do agente.
    Carrega histórico, executa o grafo LangGraph e persiste o resultado.
    """
    try:
        history = memory_service.get_history(phone)

        initial_state: AgentState = {
            "phone": phone,
            "phone_jid": phone_jid,
            "message": message,
            "name": name,
            "intent": None,
            "rag_context": None,
            "history": history,
            "response": None,
            "should_escalate": False,
            "should_send_email": False,
        }

        compiled_graph = _build_graph()
        final_state: dict = compiled_graph.invoke(initial_state)

        response = final_state.get("response") or "Vou verificar isso pra você! 🏠"
        intent = final_state.get("intent", "unknown")

        # Salvar no Redis e persistir no PostgreSQL
        memory_service.save_message(phone, "user", message)
        memory_service.save_message(phone, "assistant", response)
        memory_service.persist_conversation(phone, message, response, intent)

        # Enviar resposta ao cliente via WhatsApp
        whatsapp_service.send_message(phone_jid, response)
        logger.info(f"Ciclo do agente concluído | phone={phone} | intent={intent}")

    except Exception as e:
        logger.critical(f"run_agent error CRÍTICO | phone={phone} | {e}")
        try:
            whatsapp_service.send_message(
                phone_jid,
                "Desculpe, tive um problema técnico. Tente novamente em instantes! 😊",
            )
        except Exception:
            pass
