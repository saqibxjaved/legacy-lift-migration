"""Tests for user_service — migrated from UserServiceTest.java"""
import pytest
from unittest.mock import MagicMock, call
from demo.expected_output.user_service import User, UserRepository, UserService


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def service(repo: MagicMock) -> UserService:
    return UserService(repo)


class TestCreateUser:
    def test_valid_input_returns_user(self, service: UserService, repo: MagicMock) -> None:
        saved = User(username="alice", email="alice@example.com", id=1)
        repo.save.return_value = saved

        result = service.create_user("alice", "alice@example.com")

        assert result.username == "alice"
        assert result.email == "alice@example.com"
        repo.save.assert_called_once()

    def test_blank_username_raises(self, service: UserService) -> None:
        with pytest.raises(ValueError, match="blank"):
            service.create_user("", "alice@example.com")

    def test_whitespace_username_raises(self, service: UserService) -> None:
        with pytest.raises(ValueError, match="blank"):
            service.create_user("   ", "alice@example.com")

    def test_username_too_long_raises(self, service: UserService) -> None:
        with pytest.raises(ValueError, match="exceed"):
            service.create_user("a" * 51, "alice@example.com")

    def test_username_max_length_allowed(self, service: UserService, repo: MagicMock) -> None:
        repo.save.return_value = User(username="a" * 50, email="x@x.com")
        # Should not raise
        service.create_user("a" * 50, "x@x.com")

    def test_invalid_email_no_at_raises(self, service: UserService) -> None:
        with pytest.raises(ValueError, match="email"):
            service.create_user("alice", "not-an-email")

    def test_email_lowercased(self, service: UserService, repo: MagicMock) -> None:
        repo.save.return_value = User(username="alice", email="alice@example.com")
        service.create_user("alice", "ALICE@EXAMPLE.COM")
        saved_user = repo.save.call_args[0][0]
        assert saved_user.email == "alice@example.com"

    def test_username_trimmed(self, service: UserService, repo: MagicMock) -> None:
        repo.save.return_value = User(username="alice", email="alice@example.com")
        service.create_user("  alice  ", "alice@example.com")
        saved_user = repo.save.call_args[0][0]
        assert saved_user.username == "alice"


class TestGetUserById:
    def test_valid_id_returns_user(self, service: UserService, repo: MagicMock) -> None:
        user = User(username="alice", email="alice@example.com", id=1)
        repo.find_by_id.return_value = user

        result = service.get_user_by_id(1)

        assert result is not None
        assert result.username == "alice"

    def test_negative_id_returns_none(self, service: UserService) -> None:
        assert service.get_user_by_id(-1) is None

    def test_zero_id_returns_none(self, service: UserService) -> None:
        assert service.get_user_by_id(0) is None

    def test_none_id_returns_none(self, service: UserService) -> None:
        assert service.get_user_by_id(None) is None

    def test_not_found_returns_none(self, service: UserService, repo: MagicMock) -> None:
        repo.find_by_id.return_value = None
        assert service.get_user_by_id(999) is None


class TestGetActiveUsers:
    def test_returns_list_of_active_users(self, service: UserService, repo: MagicMock) -> None:
        active = [
            User(username="alice", email="alice@example.com"),
            User(username="bob", email="bob@example.com"),
        ]
        repo.find_by_active_true.return_value = active
        result = service.get_active_users()
        assert len(result) == 2

    def test_returns_empty_list_when_none_active(self, service: UserService, repo: MagicMock) -> None:
        repo.find_by_active_true.return_value = []
        assert service.get_active_users() == []


class TestActivateUser:
    def test_existing_user_is_activated(self, service: UserService, repo: MagicMock) -> None:
        user = User(username="alice", email="alice@example.com", active=False)
        repo.find_by_id.return_value = user
        repo.save.return_value = user

        service.activate_user(1)

        assert user.active is True
        repo.save.assert_called_once_with(user)

    def test_user_not_found_raises(self, service: UserService, repo: MagicMock) -> None:
        repo.find_by_id.return_value = None
        with pytest.raises(RuntimeError, match="User not found"):
            service.activate_user(99)


class TestDeleteUser:
    def test_existing_user_is_deleted(self, service: UserService, repo: MagicMock) -> None:
        user = User(username="alice", email="alice@example.com", id=1)
        repo.find_by_id.return_value = user

        service.delete_user(1)

        repo.delete_by_id.assert_called_once_with(1)

    def test_nonexistent_user_is_noop(self, service: UserService, repo: MagicMock) -> None:
        repo.find_by_id.return_value = None
        service.delete_user(999)
        repo.delete_by_id.assert_not_called()


class TestGetUserCount:
    def test_returns_repository_count(self, service: UserService, repo: MagicMock) -> None:
        repo.count.return_value = 42
        assert service.get_user_count() == 42
