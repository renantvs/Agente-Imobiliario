from enum import Enum
from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel


class Intent(str, Enum):
    agendamento = "agendamento"
    qualificacao = "qualificacao"
    documentacao = "documentacao"
    atendimento_humano = "atendimento_humano"
    cumprimento = "cumprimento"
    indefinido = "indefinido"


class ClassifiedIntent(TypedDict):
    """Saída estruturada do classificador de intenção."""
    intencao: str
    confianca: str          # "alta" | "media" | "baixa"
    entidades: Dict[str, Any]


class IncomingMessage(BaseModel):
    """Schema legado mantido para compatibilidade interna."""
    phone: str
    phone_jid: str
    message: str
    message_id: Optional[str] = None
    name: Optional[str] = None


class AgentState(TypedDict):
    # Identidade do usuário
    phone: str
    phone_jid: str
    name: str

    # Mensagem atual
    message: str
    message_id: str

    # Classificação de intenção
    intent: Optional[str]
    classified_intent: Optional[ClassifiedIntent]

    # Contexto RAG (desabilitado temporariamente — dimensão de vetor incompatível)
    rag_context: Optional[str]

    # Histórico da sessão genérica (para agentes sem chave isolada)
    history: List[dict]

    # Resultado do agente
    response: Optional[str]

    # Flags de controle de fluxo
    should_escalate: bool
    should_send_email: bool
