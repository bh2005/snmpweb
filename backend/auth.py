"""HTTP-Basic-Auth gegen users.yaml, mit Rollen admin/viewer."""

import secrets
from dataclasses import dataclass
from pathlib import Path

import yaml
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

USERS_FILE = Path(__file__).resolve().parent / "users.yaml"

security = HTTPBasic()


@dataclass
class User:
    username: str
    role: str


def _load_users() -> list[dict]:
    if not USERS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=f"{USERS_FILE.name} fehlt (siehe users.example.yaml)",
        )
    data = yaml.safe_load(USERS_FILE.read_text(encoding="utf-8")) or {}
    return data.get("users", [])


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> User:
    for entry in _load_users():
        username_ok = secrets.compare_digest(
            credentials.username, str(entry.get("username", ""))
        )
        password_ok = secrets.compare_digest(
            credentials.password, str(entry.get("password", ""))
        )
        if username_ok and password_ok:
            return User(username=entry["username"], role=entry.get("role", "viewer"))

    raise HTTPException(
        status_code=401,
        detail="Falscher Benutzername oder Passwort",
        headers={"WWW-Authenticate": "Basic"},
    )


def require_admin(user: User = Depends(require_auth)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Nur für Admins")
    return user
