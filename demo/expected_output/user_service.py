"""Migrated from UserService.java — com.example.monolith.service
   Extended with AdminService — migrated from admin.java (Admin Swing JFrame).
   GUI and JDBC layers stripped; pure business logic extracted as a service class.
"""
from __future__ import annotations

from typing import Optional
from dataclasses import dataclass
from enum import Enum


# ─────────────────────────────────────────────────────────────────────────────
# Stub models (replace with your actual ORM models)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class User:
    """Represents a system user."""

    username: str
    email: str
    id: Optional[int] = None
    active: bool = True


class UserRepository:
    """In-memory stub — replace with a real DB repository."""

    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._counter: int = 0

    def save(self, user: User) -> User:
        """Persist and return the user."""
        if user.id is None:
            self._counter += 1
            user.id = self._counter
        self._store[user.id] = user
        return user

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Return user by id, or None if not found."""
        return self._store.get(user_id)

    def find_by_active_true(self) -> list[User]:
        """Return all active users."""
        return [u for u in self._store.values() if u.active]

    def delete_by_id(self, user_id: int) -> None:
        """Remove user by id."""
        self._store.pop(user_id, None)

    def count(self) -> int:
        """Return total user count."""
        return len(self._store)


# ─────────────────────────────────────────────────────────────────────────────
# UserService
# ─────────────────────────────────────────────────────────────────────────────

class UserService:
    """Service for managing user lifecycle operations."""

    MAX_USERNAME_LENGTH: int = 50

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def create_user(self, username: str, email: str) -> User:
        """Create a new user after validating the provided data.

        Raises:
            ValueError: if username is blank, too long, or email is invalid.
        """
        if not username or not username.strip():
            raise ValueError("Username must not be blank")
        if len(username) > self.MAX_USERNAME_LENGTH:
            raise ValueError(
                f"Username must not exceed {self.MAX_USERNAME_LENGTH} characters"
            )
        if not email or "@" not in email:
            raise ValueError("Invalid email address")

        user = User(username=username.strip(), email=email.lower())
        return self._user_repository.save(user)

    def get_user_by_id(self, user_id: Optional[int]) -> Optional[User]:
        """Retrieve a user by ID. Returns None if not found or ID is invalid."""
        if user_id is None or user_id <= 0:
            return None
        return self._user_repository.find_by_id(user_id)

    def get_active_users(self) -> list[User]:
        """Return all active users in the system."""
        return self._user_repository.find_by_active_true()

    def activate_user(self, user_id: int) -> None:
        """Activate a user account by ID.

        Raises:
            RuntimeError: if the user is not found.
        """
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            raise RuntimeError(f"User not found: {user_id}")
        user.active = True
        self._user_repository.save(user)

    def delete_user(self, user_id: int) -> None:
        """Delete a user by ID. No-op if user does not exist."""
        if self._user_repository.find_by_id(user_id) is not None:
            self._user_repository.delete_by_id(user_id)

    def get_user_count(self) -> int:
        """Return the total count of registered users."""
        return self._user_repository.count()


# ─────────────────────────────────────────────────────────────────────────────
# AdminService  (migrated from admin.java)
# Extracted business logic from the Swing GUI admin panel.
# GUI layer (JFrame, JTable, JOptionPane) and JDBC layer dropped —
# replaced by a pure service class operating on an injectable repository.
# ─────────────────────────────────────────────────────────────────────────────

class SignupStatus(Enum):
    """Valid states for a signup record.

    Note: 'panding' (sic) is preserved as PENDING here — the original Java
    source stored the literal string 'panding' due to a typo. The migrated
    code normalises to 'pending' / 'approved' so downstream queries are
    consistent. The SignupStatus enum enforces valid values at the type level.
    """

    PENDING = "pending"
    APPROVED = "approved"


@dataclass
class SignupRecord:
    """Represents a hotel signup record — maps to the 'signup' DB table.

    Columns: name, email, password, security_question, answer, status.
    Migrated from the raw ResultSet columns read in admin.java: s().
    """

    name: str
    email: str
    password: str
    security_question: str
    answer: str
    status: SignupStatus = SignupStatus.PENDING


class SignupRepository:
    """In-memory stub for the signup table — replace with a real DB repository.

    The original admin.java accessed this table via raw JDBC with hardcoded
    credentials (root/Sudhir@123). All credential and connection logic has
    been removed; inject a real repository implementation at construction time.
    """

    def __init__(self) -> None:
        self._store: dict[str, SignupRecord] = {}  # keyed by email

    def find_all(self) -> list[SignupRecord]:
        """Return all signup records."""
        return list(self._store.values())

    def find_by_email(self, email: str) -> Optional[SignupRecord]:
        """Return the signup record for the given email, or None."""
        return self._store.get(email.lower())

    def save(self, record: SignupRecord) -> SignupRecord:
        """Persist and return the record (keyed by email)."""
        self._store[record.email.lower()] = record
        return record


class AdminService:
    """Service layer extracted from admin.java (Admin Swing JFrame).

    Original operations performed directly inside Swing event handlers via
    raw JDBC have been decomposed into three clean service methods:

      get_all_records()         ← admin.s()  (load all signup rows)
      find_by_email(email)      ← jButton1ActionPerformed  (search by email)
      toggle_status(email)      ← jTable1MouseClicked  (double-click status flip)

    Security fix: hardcoded DB credentials removed. JDBC replaced by
    injectable SignupRepository. 'panding' typo normalised to PENDING enum.
    """

    def __init__(self, signup_repository: SignupRepository) -> None:
        self._repo = signup_repository

    def get_all_records(self) -> list[SignupRecord]:
        """Return all signup records.

        Migrated from admin.java: s()
        Original SQL: SELECT * FROM signup
        """
        return self._repo.find_all()

    def find_by_email(self, email: str) -> Optional[SignupRecord]:
        """Return the signup record matching the given email, or None.

        Migrated from admin.java: jButton1ActionPerformed()
        Original SQL: SELECT * FROM signup WHERE email = ?
        Returns None (instead of showing a dialog) when no record is found —
        callers decide how to handle the absent case.

        Raises:
            ValueError: if email is blank.
        """
        if not email or not email.strip():
            raise ValueError("Email must not be blank")
        return self._repo.find_by_email(email.strip())

    def toggle_status(self, email: str) -> SignupRecord:
        """Flip a signup record's status between PENDING and APPROVED.

        Migrated from admin.java: jTable1MouseClicked() (double-click handler)
        Original SQL: UPDATE signup SET status = ? WHERE email = ?

        Business rule (preserved from original):
          PENDING  → APPROVED
          APPROVED → PENDING

        Note: the original Java stored 'panding' (typo). This implementation
        uses the SignupStatus enum so the value is always valid.

        Raises:
            ValueError: if email is blank or no record found for that email.
        """
        if not email or not email.strip():
            raise ValueError("Email must not be blank")
        record = self._repo.find_by_email(email.strip())
        if record is None:
            raise ValueError(f"No signup record found for email: {email}")
        record.status = (
            SignupStatus.APPROVED
            if record.status == SignupStatus.PENDING
            else SignupStatus.PENDING
        )
        return self._repo.save(record)
