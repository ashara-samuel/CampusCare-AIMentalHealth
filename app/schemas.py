"""Request/response models. Pydantic validates and bounds every input."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    display_name: str


class NoteIn(BaseModel):
    title: str = Field(default="Untitled", max_length=200)
    text: str = Field(default="", max_length=20_000)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    text: str
    created_at: datetime
    updated_at: datetime


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)


class ChatOut(BaseModel):
    reply: str
    crisis_detected: bool
    elevated: bool = False          # heightened concern, not acute crisis
    resources: list[dict] = []


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
