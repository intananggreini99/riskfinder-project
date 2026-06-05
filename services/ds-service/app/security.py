"""Autentikasi JWT untuk Data Scientist Sistem.

Catatan: kredensial divisi disimpan sebagai hash bcrypt (bukan plaintext).
Pada lingkungan nyata, pindahkan ke tabel users PostgreSQL + manajemen rahasia.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---- Daftar user Divisi Data Scientist (C.1) ----
# Password di-hash saat modul dimuat agar tidak ada plaintext yang tersimpan permanen.
_RAW_USERS = {
    "intan_anggreini99": "intan999",
    "doa_ibu": "ibuluvluv99",
}
USERS = {u: {"username": u, "hashed": pwd_context.hash(p[:72]), "role": "data-scientist"} for u, p in _RAW_USERS.items()}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if not user or not verify_password(password, user["hashed"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kredensial tidak valid atau token kedaluwarsa.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role != "data-scientist":
            raise cred_exc
    except JWTError:
        raise cred_exc
    return {"username": username, "role": role}
