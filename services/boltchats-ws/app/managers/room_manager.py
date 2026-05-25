import structlog

logger = structlog.get_logger()


class RoomManager:
    """In-memory room membership tracker (per process).

    Tracks which user_ids are in which rooms on this pod.
    Redis presence (PresenceManager) reflects the cluster-wide view.
    """

    def __init__(self) -> None:
        self._room_members: dict[str, set[str]] = {}  # room_id → {user_id}
        self._user_rooms: dict[str, set[str]] = {}    # user_id → {room_id}

    def join(self, user_id: str, room_id: str) -> None:
        self._room_members.setdefault(room_id, set()).add(user_id)
        self._user_rooms.setdefault(user_id, set()).add(room_id)
        logger.info("room_manager.joined", user_id=user_id, room_id=room_id)

    def leave(self, user_id: str, room_id: str) -> None:
        self._room_members.get(room_id, set()).discard(user_id)
        self._user_rooms.get(user_id, set()).discard(room_id)
        if not self._room_members.get(room_id):
            self._room_members.pop(room_id, None)
        logger.info("room_manager.left", user_id=user_id, room_id=room_id)

    def leave_all(self, user_id: str) -> list[str]:
        """Remove user from all rooms and return the list of room_ids."""
        rooms = list(self._user_rooms.pop(user_id, set()))
        for room_id in rooms:
            self._room_members.get(room_id, set()).discard(user_id)
            if not self._room_members.get(room_id):
                self._room_members.pop(room_id, None)
        logger.info("room_manager.left_all", user_id=user_id, rooms=rooms)
        return rooms

    def get_members(self, room_id: str) -> set[str]:
        return set(self._room_members.get(room_id, set()))

    def is_member(self, user_id: str, room_id: str) -> bool:
        return user_id in self._room_members.get(room_id, set())

    def get_user_rooms(self, user_id: str) -> set[str]:
        return set(self._user_rooms.get(user_id, set()))
