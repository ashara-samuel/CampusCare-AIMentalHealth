"""Counselor chat with memory + a two-layer safety gate (run BEFORE the model):

  1. rule-based detector (crisis.py)  — the guaranteed floor, catches explicit risk
  2. model-based classifier (classifier.py) — catches subtler signals

On 'crisis' (from either layer) the LLM is never called — the user gets a caring
hand-off to real help. On 'elevated', the student still gets a supportive reply,
with resources gently attached.

Conversation history is persisted per user so the counselor has continuity across
messages. It is sensitive content: scoped to the owning user, never logged, and
clearable via DELETE /chat/history. The crisis gate runs on every new message
regardless of history.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..models import Message, User
from ..safety.classifier import classify
from ..safety.crisis import crisis_response, detect_crisis, support_resources
from ..safety.guardrails import build_messages
from ..schemas import ChatIn, ChatOut, MessageOut
from ..services.llm import generate_reply

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


def _recent_history(db: Session, user: User) -> list[dict]:
    """The last N turns for this user, oldest first, as LLM messages."""
    rows = db.scalars(
        select(Message).where(Message.user_id == user.id)
        .order_by(Message.id.desc()).limit(settings.chat_history_window)
    ).all()
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _save(db: Session, user: User, role: str, content: str) -> None:
    db.add(Message(user_id=user.id, role=role, content=content))
    db.commit()


@router.post("", response_model=ChatOut)
def chat(body: ChatIn, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)) -> ChatOut:
    region = settings.crisis_hotline_region

    # Safety gate — a crisis never reaches the LLM, with or without history.
    is_crisis = detect_crisis(body.message)
    level = "crisis" if is_crisis else classify(body.message)

    if level == "crisis":
        text, resources = crisis_response(region)
        _save(db, user, "user", body.message)
        _save(db, user, "assistant", text)
        return ChatOut(reply=text, crisis_detected=True, resources=resources)

    # Normal path: give the model the recent conversation as context.
    history = _recent_history(db, user)
    reply = generate_reply(build_messages(body.message, history))
    _save(db, user, "user", body.message)
    _save(db, user, "assistant", reply)

    if level == "elevated":
        return ChatOut(reply=reply, crisis_detected=False, elevated=True,
                       resources=support_resources(region))
    return ChatOut(reply=reply, crisis_detected=False)


@router.get("/history", response_model=list[MessageOut])
def history(db: Session = Depends(get_db),
            user: User = Depends(get_current_user)) -> list[Message]:
    return list(db.scalars(
        select(Message).where(Message.user_id == user.id).order_by(Message.id.asc())))


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> None:
    db.execute(delete(Message).where(Message.user_id == user.id))
    db.commit()
