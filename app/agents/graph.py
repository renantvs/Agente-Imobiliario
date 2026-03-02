"""
ZONA 4 — Roteador Central
ZONA 6 — Finalização explícita

Fluxo completo:
  [intent] → [router] → [agente especializado] → [finalize]

Zona 4: Um único ponto de roteamento por intenção classificada.
Nenhum agente é chamado diretamente de fora do roteador.

Zona 6: Nó finalize executa obrigatoriamente ao final de TODOS os caminhos:
  1. Deletar intent:{phone} do Redis (limpeza de estado)
  2. Persistir no PostgreSQL
  3. Salvar no histórico genérico Redis
  4. Enviar resposta via WhatsApp
"""

from loguru import logger
from langgraph.graph import StateGraph, END

from app.agents.nodes.intent_node import identify_intent
from app.agents.nodes.greeting_agent import greeting_agent
from app.agents.nodes.scheduling_agent import scheduling_agent
from app.agents.nodes.qualification_agent import qualification_agent
from app.agents.nodes.documentation_agent import documentation_agent
from app.agents.nodes.escalation_node import check_escalation, execute_escalation
from app.agents.nodes.unknown_agent import unknown_agent
from app.services import memory_service, whatsapp_service
from app.models.schemas import AgentState, Intent
from app.core.redis_client import redis_client


# ---------------------------------------------------------------------------
# Zona 4 — Roteador central explícito
# ---------------------------------------------------------------------------

def _route_by_intent(state: dict) -> str:
    """Único ponto de roteamento. Direciona pelo campo intent classificado."""
    intent = state.get("intent", Intent.indefinido.value)
    routes = {
        Intent.cumprimento.value:        "greeting",
        Intent.agendamento.value:         "scheduling",
        Intent.qualificacao.value:        "qualification",
        Intent.documentacao.value:        "documentation",
        Intent.atendimento_humano.value:  "check_escalation",
        Intent.indefinido.value:          "unknown",
    }
    destination = routes.get(intent, "unknown")
    logger.info(f"Router → {destination} | phone={state['phone']} | intent={intent}")
    return destination


def _route_after_escalation_check(state: dict) -> str:
    return "escalate" if state.get("should_escalate") else "unknown"


# ---------------------------------------------------------------------------
# Zona 6 — Finalização explícita
# ---------------------------------------------------------------------------

def finalize(state: dict) -> dict:
    """
    Zona 6 — Executado ao final de TODOS os caminhos do grafo.
    1. Deleta intent:{phone} do Redis
    2. Persiste no PostgreSQL
    3. Salva no histórico genérico Redis
    4. Envia resposta via WhatsApp
    """
    phone = state["phone"]
    phone_jid = state.get("phone_jid", "")
    message = state.get("message", "")
    intent = state.get("intent", Intent.indefinido.value)
    response = state.get("response") or (
        "Hmm, não consegui processar sua mensagem agora. Pode tentar novamente? 😊"
    )

    # 1. Limpar cache de intenção
    cache_key = f"intent:{phone}"
    redis_client.delete(cache_key)
    logger.debug(f"intent:{phone} deletado do Redis")

    # 2. Persistir no PostgreSQL
    try:
        memory_service.save_message(phone, "user", message)
        memory_service.save_message(phone, "assistant", response)
        memory_service.persist_conversation(phone, message, response, intent)
    except Exception as e:
        logger.error(f"finalize: erro ao persistir | phone={phone} | {e}")

    # 3. Enviar resposta via WhatsApp
    try:
        whatsapp_service.send_message(phone_jid, response)
        logger.info(f"Ciclo concluído | phone={phone} | intent={intent}")
    except Exception as e:
        logger.error(f"finalize: erro ao enviar mensagem | phone={phone} | {e}")

    state["response"] = response
    return state


# ---------------------------------------------------------------------------
# Construção e compilação do grafo
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph com roteador central explícito."""
    graph = StateGraph(dict)

    # Zona 3 — Classificação
    graph.add_node("intent", identify_intent)

    # Zona 4 — Roteamento
    # (sem nó próprio — implementado como conditional_edges a partir de intent)

    # Zona 5 — Agentes especializados
    graph.add_node("greeting",          greeting_agent)
    graph.add_node("scheduling",        scheduling_agent)
    graph.add_node("qualification",     qualification_agent)
    graph.add_node("documentation",     documentation_agent)
    graph.add_node("check_escalation",  check_escalation)
    graph.add_node("escalate",          execute_escalation)
    graph.add_node("unknown",           unknown_agent)

    # RAG (desabilitado — mantido no grafo caso seja reativado)

    # Zona 6 — Finalização
    graph.add_node("finalize", finalize)

    # --- Entry point ---
    graph.set_entry_point("intent")

    # --- Roteador central (Zona 4) ---
    graph.add_conditional_edges(
        "intent",
        _route_by_intent,
        {
            "greeting":         "greeting",
            "scheduling":       "scheduling",
            "qualification":    "qualification",
            "documentation":    "documentation",
            "check_escalation": "check_escalation",
            "unknown":          "unknown",
        },
    )

    # Escalação: check → escalate ou unknown (fallback)
    graph.add_conditional_edges(
        "check_escalation",
        _route_after_escalation_check,
        {"escalate": "escalate", "unknown": "unknown"},
    )

    # Todos os agentes convergem para finalize (Zona 6)
    for node in ("greeting", "scheduling", "qualification",
                 "documentation", "escalate", "unknown"):
        graph.add_edge(node, "finalize")

    graph.add_edge("finalize", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def run_agent(
    phone: str,
    phone_jid: str,
    message: str,
    name: str = "",
    message_id: str = "",
) -> None:
    """
    Ponto de entrada do agente chamado pelo message_worker (Zona 2).
    Monta o estado inicial e executa o grafo.
    """
    try:
        history = memory_service.get_history(phone)

        initial_state: AgentState = {
            "phone": phone,
            "phone_jid": phone_jid,
            "name": name,
            "message": message,
            "message_id": message_id,
            "intent": None,
            "classified_intent": None,
            "rag_context": None,
            "history": history,
            "response": None,
            "should_escalate": False,
            "should_send_email": False,
        }

        compiled_graph = _build_graph()
        compiled_graph.invoke(initial_state)

    except Exception as e:
        logger.critical(f"run_agent CRÍTICO | phone={phone} | {e}")
        # Garantir limpeza de estado mesmo em falha catastrófica
        redis_client.delete(f"intent:{phone}")
        try:
            whatsapp_service.send_message(
                phone_jid,
                "Desculpe, tive um problema técnico agora. 😊 "
                "Pode tentar novamente em instantes?",
            )
        except Exception:
            pass
