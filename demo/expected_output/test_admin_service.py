"""Tests for AdminService, SignupRepository, SignupRecord, SignupStatus.

Migrated business logic from admin.java (Admin Swing JFrame):
  - get_all_records()   ← admin.s()
  - find_by_email()     ← jButton1ActionPerformed
  - toggle_status()     ← jTable1MouseClicked (double-click toggle)

Security rule verified: no hardcoded credentials, no JDBC, injectable repo.
Status normalisation verified: 'panding' typo replaced by SignupStatus enum.
"""
import pytest
from unittest.mock import MagicMock
from demo.expected_output.user_service import (
    AdminService,
    SignupRecord,
    SignupRepository,
    SignupStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_record(
    name: str = "Alice",
    email: str = "alice@hotel.com",
    status: SignupStatus = SignupStatus.PENDING,
) -> SignupRecord:
    return SignupRecord(
        name=name,
        email=email,
        password="hashed_secret",
        security_question="Pet name?",
        answer="Fluffy",
        status=status,
    )


def make_repo() -> SignupRepository:
    return SignupRepository()


def make_service(repo: SignupRepository | None = None) -> AdminService:
    return AdminService(repo or make_repo())


# ─────────────────────────────────────────────────────────────────────────────
# TestSignupStatus — enum values and normalisation
# ─────────────────────────────────────────────────────────────────────────────

class TestSignupStatus:
    def test_pending_value_is_lowercase_pending(self):
        """PENDING must store 'pending', not 'panding' (original Java typo)."""
        assert SignupStatus.PENDING.value == "pending"

    def test_approved_value_is_lowercase_approved(self):
        assert SignupStatus.APPROVED.value == "approved"

    def test_members_are_distinct(self):
        assert SignupStatus.PENDING != SignupStatus.APPROVED


# ─────────────────────────────────────────────────────────────────────────────
# TestSignupRepository — in-memory store
# ─────────────────────────────────────────────────────────────────────────────

class TestSignupRepository:
    def test_save_and_find_by_email(self):
        repo = make_repo()
        record = make_record(email="bob@hotel.com")
        repo.save(record)
        result = repo.find_by_email("bob@hotel.com")
        assert result is not None
        assert result.name == "Alice"

    def test_find_by_email_case_insensitive(self):
        """Email lookup is case-insensitive — stored and retrieved lowercased."""
        repo = make_repo()
        repo.save(make_record(email="Bob@Hotel.COM"))
        assert repo.find_by_email("bob@hotel.com") is not None
        assert repo.find_by_email("BOB@HOTEL.COM") is not None

    def test_find_by_email_returns_none_when_not_found(self):
        repo = make_repo()
        assert repo.find_by_email("nobody@hotel.com") is None

    def test_find_all_empty(self):
        repo = make_repo()
        assert repo.find_all() == []

    def test_find_all_returns_all_records(self):
        repo = make_repo()
        repo.save(make_record(email="a@hotel.com"))
        repo.save(make_record(email="b@hotel.com"))
        assert len(repo.find_all()) == 2


# ─────────────────────────────────────────────────────────────────────────────
# TestGetAllRecords — migrated from admin.java: s()
# ─────────────────────────────────────────────────────────────────────────────

class TestGetAllRecords:
    def test_returns_all_records(self):
        """Migrated from s() — SELECT * FROM signup."""
        repo = MagicMock(spec=SignupRepository)
        repo.find_all.return_value = [make_record(), make_record(email="b@h.com")]
        service = AdminService(repo)
        result = service.get_all_records()
        assert len(result) == 2
        repo.find_all.assert_called_once()

    def test_returns_empty_list_when_no_records(self):
        repo = MagicMock(spec=SignupRepository)
        repo.find_all.return_value = []
        service = AdminService(repo)
        assert service.get_all_records() == []


# ─────────────────────────────────────────────────────────────────────────────
# TestFindByEmail — migrated from jButton1ActionPerformed
# ─────────────────────────────────────────────────────────────────────────────

class TestFindByEmail:
    def test_found_returns_record(self):
        """Migrated from jButton1ActionPerformed — SELECT * FROM signup WHERE email=?"""
        repo = MagicMock(spec=SignupRepository)
        record = make_record(email="alice@hotel.com")
        repo.find_by_email.return_value = record
        service = AdminService(repo)
        result = service.find_by_email("alice@hotel.com")
        assert result is not None
        assert result.email == "alice@hotel.com"
        repo.find_by_email.assert_called_once_with("alice@hotel.com")

    def test_not_found_returns_none(self):
        """Returns None instead of showing a JOptionPane dialog."""
        repo = MagicMock(spec=SignupRepository)
        repo.find_by_email.return_value = None
        service = AdminService(repo)
        assert service.find_by_email("ghost@hotel.com") is None

    def test_blank_email_raises(self):
        """Empty email raises ValueError — replaces the JOptionPane 'Record Not Found' dialog."""
        service = make_service()
        with pytest.raises(ValueError, match="blank"):
            service.find_by_email("")

    def test_whitespace_email_raises(self):
        service = make_service()
        with pytest.raises(ValueError, match="blank"):
            service.find_by_email("   ")

    def test_email_is_stripped_before_lookup(self):
        """Leading/trailing whitespace trimmed before querying."""
        repo = MagicMock(spec=SignupRepository)
        repo.find_by_email.return_value = None
        service = AdminService(repo)
        service.find_by_email("  alice@hotel.com  ")
        repo.find_by_email.assert_called_once_with("alice@hotel.com")


# ─────────────────────────────────────────────────────────────────────────────
# TestToggleStatus — migrated from jTable1MouseClicked (double-click handler)
# ─────────────────────────────────────────────────────────────────────────────

class TestToggleStatus:
    def test_pending_toggles_to_approved(self):
        """
        Migrated from jTable1MouseClicked: if status == 'panding' → set 'approved'.
        Normalised: PENDING → APPROVED.
        Original SQL: UPDATE signup SET status='approved' WHERE email=?
        """
        repo = make_repo()
        record = make_record(email="alice@hotel.com", status=SignupStatus.PENDING)
        repo.save(record)
        service = make_service(repo)

        result = service.toggle_status("alice@hotel.com")

        assert result.status == SignupStatus.APPROVED

    def test_approved_toggles_to_pending(self):
        """
        Migrated from jTable1MouseClicked: else branch → set 'panding' (normalised: PENDING).
        Original SQL: UPDATE signup SET status='panding' WHERE email=?
        """
        repo = make_repo()
        record = make_record(email="alice@hotel.com", status=SignupStatus.APPROVED)
        repo.save(record)
        service = make_service(repo)

        result = service.toggle_status("alice@hotel.com")

        assert result.status == SignupStatus.PENDING

    def test_toggle_persists_change(self):
        """After toggle, the repository reflects the new status."""
        repo = make_repo()
        repo.save(make_record(email="alice@hotel.com", status=SignupStatus.PENDING))
        service = make_service(repo)

        service.toggle_status("alice@hotel.com")

        stored = repo.find_by_email("alice@hotel.com")
        assert stored.status == SignupStatus.APPROVED

    def test_toggle_twice_returns_to_original_status(self):
        """Double-toggle is idempotent — status returns to initial value."""
        repo = make_repo()
        repo.save(make_record(email="alice@hotel.com", status=SignupStatus.PENDING))
        service = make_service(repo)

        service.toggle_status("alice@hotel.com")
        service.toggle_status("alice@hotel.com")

        stored = repo.find_by_email("alice@hotel.com")
        assert stored.status == SignupStatus.PENDING

    def test_blank_email_raises(self):
        service = make_service()
        with pytest.raises(ValueError, match="blank"):
            service.toggle_status("")

    def test_not_found_email_raises(self):
        """Toggle on unknown email raises ValueError — no silent failure."""
        service = make_service()
        with pytest.raises(ValueError, match="No signup record found"):
            service.toggle_status("ghost@hotel.com")

    def test_uses_mock_repo(self):
        """Verify AdminService calls the repository, not JDBC directly."""
        repo = MagicMock(spec=SignupRepository)
        record = make_record(email="alice@hotel.com", status=SignupStatus.PENDING)
        repo.find_by_email.return_value = record
        repo.save.return_value = record
        service = AdminService(repo)

        service.toggle_status("alice@hotel.com")

        repo.find_by_email.assert_called_once_with("alice@hotel.com")
        repo.save.assert_called_once()
