import pytest

from app.managers.room_manager import RoomManager


@pytest.fixture
def manager() -> RoomManager:
    return RoomManager()


def test_join_adds_user_to_room(manager):
    manager.join("user_1", "room_a")
    assert manager.is_member("user_1", "room_a")


def test_join_multiple_rooms(manager):
    manager.join("user_1", "room_a")
    manager.join("user_1", "room_b")
    assert manager.get_user_rooms("user_1") == {"room_a", "room_b"}


def test_leave_removes_user_from_room(manager):
    manager.join("user_1", "room_a")
    manager.leave("user_1", "room_a")
    assert not manager.is_member("user_1", "room_a")


def test_leave_empty_room_cleans_internal_dict(manager):
    manager.join("user_1", "room_a")
    manager.leave("user_1", "room_a")
    assert "room_a" not in manager._room_members


def test_leave_nonexistent_is_safe(manager):
    manager.leave("user_1", "room_xyz")  # must not raise


def test_get_members_returns_all_joined_users(manager):
    manager.join("user_1", "room_a")
    manager.join("user_2", "room_a")
    assert manager.get_members("room_a") == {"user_1", "user_2"}


def test_get_members_unknown_room_returns_empty(manager):
    assert manager.get_members("unknown") == set()


def test_is_member_false_for_non_member(manager):
    assert not manager.is_member("user_1", "room_a")


def test_leave_all_returns_rooms(manager):
    manager.join("user_1", "room_a")
    manager.join("user_1", "room_b")
    rooms = manager.leave_all("user_1")
    assert set(rooms) == {"room_a", "room_b"}


def test_leave_all_cleans_membership(manager):
    manager.join("user_1", "room_a")
    manager.leave_all("user_1")
    assert not manager.is_member("user_1", "room_a")
    assert manager.get_user_rooms("user_1") == set()


def test_leave_all_unknown_user_returns_empty(manager):
    assert manager.leave_all("nobody") == []


def test_multiple_users_in_same_room(manager):
    manager.join("user_1", "room_a")
    manager.join("user_2", "room_a")
    manager.leave("user_1", "room_a")
    assert manager.is_member("user_2", "room_a")
    assert "room_a" in manager._room_members
