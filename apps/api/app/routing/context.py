from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import Message


@dataclass(frozen=True)
class SelectedContext:
    prompt: str
    mode: str
    message_count: int


class ContextSelectionService:
    def __init__(self, max_chars: int = 12000) -> None:
        self.max_chars = max_chars

    def select(
        self, db: Session, conversation_id: str, prompt: str, include_history: bool
    ) -> SelectedContext:
        if not include_history:
            return SelectedContext(prompt, "none", 0)
        messages = db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
        ).all()
        lines = [f"{message.role}: {message.content}" for message in reversed(messages)]
        history = "\n".join(lines)
        combined = f"Conversation context:\n{history}\n\nUser request:\n{prompt}"
        if len(combined) <= self.max_chars:
            return SelectedContext(combined, "recent", len(messages))
        prefix = "Conversation summary (older context compacted):\n"
        tail = combined[-max(0, self.max_chars - len(prefix)) :]
        summary = f"{prefix}{tail}"
        return SelectedContext(summary, "summarized", len(messages))
