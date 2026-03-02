from dataclasses import dataclass, field


@dataclass
class MessageContext:
    """
    Objeto de contexto central montado UMA ÚNICA VEZ no webhook e propagado
    por todas as zonas do sistema sem remontagem ou reinterpretação.

    phone      → apenas dígitos — usado para Redis, banco e logs
    phone_jid  → JID completo (ex: 5521x@s.whatsapp.net) — usado APENAS para enviar mensagem
    name       → nome de exibição do WhatsApp (pushName)
    content    → texto normalizado da mensagem
    message_id → ID único da mensagem (key.id) — usado para deduplicação no buffer
    """

    phone: str
    phone_jid: str
    name: str
    content: str
    message_id: str = field(default="")
