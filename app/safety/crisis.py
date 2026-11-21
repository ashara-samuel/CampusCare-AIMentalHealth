"""Crisis detection + escalation.

This is the most important module in the app. When a user shows signs of a
mental-health crisis (self-harm / suicidal ideation), the bot's job is NOT to
counsel them through it — it is to respond with care and route them to real,
immediate human help.

The detector here is a deterministic first layer (fast, testable, no false
negatives on explicit phrasing). In production it should be paired with a
model-based classifier; this layer is the floor, not the ceiling. It is tuned to
over-escalate rather than miss: a borderline case returns a crisis response.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Signals of acute risk. Matched case-insensitively on word-ish boundaries.
# Intentionally broad; false positives here are acceptable, misses are not.
_CRISIS_PATTERNS = [
    r"\bkill myself\b", r"\bkilling myself\b", r"\bend my life\b", r"\bend it all\b",
    r"\bsuicid", r"\btake my (own )?life\b", r"\bdon'?t want to (live|be alive|wake up)\b",
    r"\bwant to die\b", r"\bbetter off dead\b", r"\bno reason to live\b",
    r"\bself[\s-]?harm\b", r"\bhurt myself\b", r"\bharm myself\b", r"\bcut myself\b",
    r"\bno way out\b", r"\bcan'?t go on\b", r"\bgive up on life\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


@dataclass(frozen=True)
class CrisisResource:
    name: str
    contact: str
    note: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "contact": self.contact, "note": self.note}


def _resources(region: str = "international") -> list[CrisisResource]:
    """Baseline, widely-applicable resources. Extend per deployment region."""
    return [
        CrisisResource("Local emergency services",
                       "Call your local emergency number (e.g. 112, 911, 999)",
                       "If you are in immediate danger."),
        CrisisResource("988 Suicide & Crisis Lifeline (US)", "Call or text 988",
                       "24/7, free and confidential (US)."),
        CrisisResource("Crisis Text Line", "Text HOME to 741741",
                       "24/7 text support (US, UK, CA, IE)."),
        CrisisResource("Find a Helpline", "https://findahelpline.com",
                       "Free, confidential helplines in your country."),
    ]


def detect_crisis(message: str) -> bool:
    return any(p.search(message) for p in _COMPILED)


def support_resources(region: str = "international") -> list[dict]:
    """Resources to attach to an 'elevated' (not acute) reply — gentle signposting
    alongside a normal supportive conversation."""
    return [r.as_dict() for r in _resources(region)]


def crisis_response(region: str = "international") -> tuple[str, list[dict]]:
    """The message + resources returned INSTEAD of an LLM reply on crisis."""
    text = (
        "I'm really glad you reached out, and I'm concerned about what you're going "
        "through. I'm an AI and not able to help with something this serious on my "
        "own — but you deserve support from a real person right now, and help is "
        "available. Please reach out to one of the resources below, or to someone you "
        "trust. You don't have to go through this alone, and reaching out is a strong "
        "thing to do."
    )
    return text, [r.as_dict() for r in _resources(region)]
