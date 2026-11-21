"""Voice output: synthesize the counselor's reply to speech.

Auth-required (so it isn't an open TTS proxy on your key), length-bounded via the
schema, and content is never logged. Speech-to-TEXT (the mic) is done entirely in
the browser, so a student's audio never leaves their device — only the final text
is sent, through the same auth + safety path as typed chat.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..deps import get_current_user
from ..models import User
from ..schemas import SpeakIn
from ..services.tts import TTSUnavailable, synthesize

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/speak")
def speak(body: SpeakIn, user: User = Depends(get_current_user)) -> Response:
    try:
        audio = synthesize(body.text)
    except TTSUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
    return Response(content=audio, media_type="audio/mpeg")
