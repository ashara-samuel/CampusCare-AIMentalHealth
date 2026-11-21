"""Counselor chat with a two-layer safety gate, run BEFORE the model:

  1. rule-based detector (crisis.py)  — the guaranteed floor, catches explicit risk
  2. model-based classifier (classifier.py) — catches subtler signals

On 'crisis' (from either layer) the LLM is never called — the user gets a caring
hand-off to real help. On 'elevated', the student still gets a supportive reply,
with resources gently attached. Message content is never logged.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import get_settings
from ..deps import get_current_user
from ..models import User
from ..safety.classifier import classify
from ..safety.crisis import crisis_response, detect_crisis, support_resources
from ..safety.guardrails import build_messages
from ..schemas import ChatIn, ChatOut
from ..services.llm import generate_reply

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


@router.post("", response_model=ChatOut)
def chat(body: ChatIn, user: User = Depends(get_current_user)) -> ChatOut:
    region = settings.crisis_hotline_region

    # Layer 1: deterministic floor.
    if detect_crisis(body.message):
        text, resources = crisis_response(region)
        return ChatOut(reply=text, crisis_detected=True, resources=resources)

    # Layer 2: model classifier for subtler signals.
    level = classify(body.message)
    if level == "crisis":
        text, resources = crisis_response(region)
        return ChatOut(reply=text, crisis_detected=True, resources=resources)

    reply = generate_reply(build_messages(body.message))
    if level == "elevated":
        return ChatOut(reply=reply, crisis_detected=False, elevated=True,
                       resources=support_resources(region))
    return ChatOut(reply=reply, crisis_detected=False)
