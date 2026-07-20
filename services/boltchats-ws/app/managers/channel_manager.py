import structlog
from collections import defaultdict

logger = structlog.get_logger()


class ChannelManager:
    """Manages WebSocket connections per workspace and channel (v2).
    
    In-memory state per pod — tracks which users are connected to which
    workspace/channel combination. Used for routing messages to local connections.
    """

    def __init__(self) -> None:
        # workspace_id → {channel_id → set(user_ids)}
        self._workspace_channels: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        # (workspace_id, channel_id) → set(user_ids)
        self._channel_members: dict[tuple[str, str], set[str]] = defaultdict(set)
        # (workspace_id, dm_id) → set(user_ids)
        self._dm_members: dict[tuple[str, str], set[str]] = defaultdict(set)

    def join_channel(self, workspace_id: str, channel_id: str, user_id: str) -> None:
        """Add user to channel member list."""
        key = (workspace_id, channel_id)
        self._channel_members[key].add(user_id)
        self._workspace_channels[workspace_id][channel_id].add(user_id)
        logger.debug(
            "channel_manager.join_channel",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

    def leave_channel(self, workspace_id: str, channel_id: str, user_id: str) -> None:
        """Remove user from channel member list."""
        key = (workspace_id, channel_id)
        self._channel_members[key].discard(user_id)
        self._workspace_channels[workspace_id][channel_id].discard(user_id)
        
        # Clean up empty entries
        if not self._channel_members[key]:
            del self._channel_members[key]
        if not self._workspace_channels[workspace_id][channel_id]:
            del self._workspace_channels[workspace_id][channel_id]
        
        logger.debug(
            "channel_manager.leave_channel",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

    def join_dm(self, workspace_id: str, dm_id: str, user_id: str) -> None:
        """Add user to DM group member list."""
        key = (workspace_id, dm_id)
        self._dm_members[key].add(user_id)
        logger.debug(
            "channel_manager.join_dm",
            workspace_id=workspace_id,
            dm_id=dm_id,
            user_id=user_id,
        )

    def leave_dm(self, workspace_id: str, dm_id: str, user_id: str) -> None:
        """Remove user from DM group member list."""
        key = (workspace_id, dm_id)
        self._dm_members[key].discard(user_id)
        
        # Clean up empty entries
        if not self._dm_members[key]:
            del self._dm_members[key]
        
        logger.debug(
            "channel_manager.leave_dm",
            workspace_id=workspace_id,
            dm_id=dm_id,
            user_id=user_id,
        )

    def get_channel_members(self, workspace_id: str, channel_id: str) -> set[str]:
        """Get all local members connected to a channel."""
        key = (workspace_id, channel_id)
        return self._channel_members.get(key, set()).copy()

    def get_dm_members(self, workspace_id: str, dm_id: str) -> set[str]:
        """Get all local members connected to a DM group."""
        key = (workspace_id, dm_id)
        return self._dm_members.get(key, set()).copy()

    def get_workspace_members(self, workspace_id: str) -> set[str]:
        """Get all local members connected to any channel in workspace."""
        all_members = set()
        for channel_members in self._workspace_channels.get(workspace_id, {}).values():
            all_members.update(channel_members)
        return all_members

    def get_user_channels(self, workspace_id: str, user_id: str) -> set[str]:
        """Get all channels a user is connected to in a workspace."""
        channels = set()
        for channel_id, members in self._workspace_channels.get(workspace_id, {}).items():
            if user_id in members:
                channels.add(channel_id)
        return channels

    def get_user_dms(self, workspace_id: str, user_id: str) -> set[str]:
        """Get all DM groups a user is connected to in a workspace."""
        dms = set()
        for (ws_id, dm_id), members in self._dm_members.items():
            if ws_id == workspace_id and user_id in members:
                dms.add(dm_id)
        return dms

    def disconnect_user(self, workspace_id: str, user_id: str) -> dict:
        """Disconnect user from all channels and DMs, return cleanup info."""
        channels = self.get_user_channels(workspace_id, user_id)
        dms = self.get_user_dms(workspace_id, user_id)
        
        for channel_id in channels:
            self.leave_channel(workspace_id, channel_id, user_id)
        
        for dm_id in dms:
            self.leave_dm(workspace_id, dm_id, user_id)
        
        return {"channels": channels, "dms": dms}
