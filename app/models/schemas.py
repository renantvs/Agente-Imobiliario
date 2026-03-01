from enum import Enum
from typing import Optional, List
from typing_extensions import TypedDict
from pydantic import BaseModel


class Intent(str, Enum):
    faq = "faq"
    property_search = "property_search"
    schedule_visit = "schedule_visit"
    lead_capture = "lead_capture"
    escalation = "escalation"
    greeting = "greeting"
    unknown = "unknown"


class IncomingMessage(BaseModel):
    phone: str
    message: str
    message_id: Optional[str] = None
    name: Optional[str] = None


class AgentState(TypedDict):
    phone: str
    message: str
    name: str
    intent: Optional[str]
    rag_context: Optional[str]
    history: List[dict]
    response: Optional[str]
    should_escalate: bool
    should_send_email: bool
