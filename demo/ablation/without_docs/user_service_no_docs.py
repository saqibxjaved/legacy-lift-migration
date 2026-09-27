"""
Migrated from UserService.java — WITHOUT document context (no ADRs, no Javadoc).

ABLATION VARIANT: This file represents what a migration agent produces when it has
NO access to project documentation (pom.xml CVEs, ADR constraints, Javadoc intent).
It is intentionally degraded to demonstrate the impact of document understanding.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    username: str
    email: str
    id: Optional[int] = None
    active: bool = True


class UserRepository:
    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._counter: int = 0

    def save(self, user: User) -> User:
        if user.id is None:
            self._counter += 1
            user.id = self._counter
        self._store[user.id] = user
        return user

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._store.get(user_id)

    def find_by_active_true(self) -> list[User]:
        return [u for u in self._store.values() if u.active]

    def delete_by_id(self, user_id: int) -> None:
        self._store.pop(user_id, None)

    def count(self) -> int:
        return len(self._store)


class UserService:
    """User management service."""

    # CONSTRAINT VIOLATION 1 (ADR-003): magic number instead of named constant
    # Without Javadoc context, agent does not know this is a regulatory requirement
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def create_user(self, username: str, email: str) -> User:
        # CONSTRAINT VIOLATION 2 (ADR-003): missing username.strip() — Javadoc said
        # "Normalises input (trim, lowercase)" but agent had no Javadoc to read
        if not username:
            raise ValueError("Username must not be blank")
        # CONSTRAINT VIOLATION 3 (ADR-003): magic number 50 — not a named constant
        if len(username) > 50:
            raise ValueError("Username too long")
        if not email or "@" not in email:
            raise ValueError("Invalid email")

        # CONSTRAINT VIOLATION 4 (ADR-003): email NOT lowercased — agent missed this
        # without Javadoc stating "email.lower() before saving (case-insensitive storage)"
        user = User(username=username, email=email)
        return self._user_repository.save(user)

    def get_user_by_id(self, user_id: Optional[int]) -> Optional[User]:
        if user_id is None or user_id <= 0:
            return None
        return self._user_repository.find_by_id(user_id)

    def get_active_users(self) -> list[User]:
        return self._user_repository.find_by_active_true()

    def activate_user(self, user_id: int) -> None:
        # CONSTRAINT VIOLATION 5 (ADR-003 / Javadoc): Javadoc says "Throws if user
        # not found — this is intentional (hard error, not soft one)" but without
        # that context the agent returns silently instead of raising RuntimeError
        user = self._user_repository.find_by_id(user_id)
        if user is not None:
            user.active = True
            self._user_repository.save(user)
        # Silent no-op on missing user — WRONG per Javadoc business rule

    def delete_user(self, user_id: int) -> None:
        if self._user_repository.find_by_id(user_id) is not None:
            self._user_repository.delete_by_id(user_id)

    def get_user_count(self) -> int:
        return self._user_repository.count()
