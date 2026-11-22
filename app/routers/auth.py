"""Registration and login. Passwords are bcrypt-hashed; a JWT is returned."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Message, Note, User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    exists = db.scalar(select(User).where(User.email == body.email))
    if exists:
        # Same message/shape as a generic failure — don't confirm which emails exist.
        raise HTTPException(status.HTTP_409_CONFLICT, "Could not register with those details")
    user = User(email=body.email, password_hash=hash_password(body.password),
                display_name=body.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    # Constant-ish: always run verify to avoid a trivial user-enumeration timing gap.
    ok = verify_password(body.password, user.password_hash) if user else \
        verify_password(body.password, "$2b$12$" + "x" * 53)
    if not user or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> None:
    """Permanently delete the account and ALL of its data.

    Required by the App Store and Google Play for apps with accounts. We delete
    the user's messages and notes explicitly (so it works on SQLite too, where FK
    cascade isn't on by default) and then the user. Irreversible.
    """
    db.execute(delete(Message).where(Message.user_id == user.id))
    db.execute(delete(Note).where(Note.user_id == user.id))
    db.delete(user)
    db.commit()
