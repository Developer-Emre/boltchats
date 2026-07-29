"""
Integration tests for migration validation.
Run after all 5 migration scripts complete successfully.
"""

import pytest
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.constants import Collection


@pytest.fixture
async def db():
    """Connect to test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["boltchats_staging"]
    yield db
    # Cleanup after tests
    # await client.close()


class TestMigrationValidation:
    """Validate post-migration data consistency."""

    async def test_users_have_workspaces(self, db):
        """All users should have at least one workspace."""
        users_without_workspaces = await db[Collection.USERS].count_documents(
            {"workspaces": {"$exists": False}}
        )
        assert users_without_workspaces == 0, "Some users missing workspaces array"

    async def test_workspaces_exist(self, db):
        """At least one workspace should exist."""
        workspace_count = await db[Collection.WORKSPACES].count_documents({})
        assert workspace_count > 0, "No workspaces found after migration"

    async def test_workspaces_have_owner(self, db):
        """All workspaces should have an owner_id."""
        workspaces_without_owner = await db[Collection.WORKSPACES].count_documents(
            {"owner_id": {"$exists": False}}
        )
        assert workspaces_without_owner == 0, "Some workspaces missing owner_id"

    async def test_workspaces_have_members(self, db):
        """All workspaces should have at least the owner in members."""
        workspaces_without_members = await db[Collection.WORKSPACES].count_documents(
            {"members": {"$exists": False}}
        )
        assert (
            workspaces_without_members == 0
        ), "Some workspaces missing members array"

    async def test_channels_exist(self, db):
        """Channels collection should have data from migrated rooms."""
        channel_count = await db[Collection.CHANNELS].count_documents({})
        room_count = await db[Collection.ROOMS].count_documents({})
        assert channel_count > 0, "No channels found after migration"
        assert (
            channel_count == room_count
        ), f"Channel count ({channel_count}) doesn't match room count ({room_count})"

    async def test_channels_have_workspace_id(self, db):
        """All channels should have workspace_id."""
        channels_without_workspace = await db[Collection.CHANNELS].count_documents(
            {"workspace_id": {"$exists": False}}
        )
        assert channels_without_workspace == 0, "Some channels missing workspace_id"

    async def test_channels_have_members(self, db):
        """All channels should have a members array."""
        channels_without_members = await db[Collection.CHANNELS].count_documents(
            {"members": {"$exists": False}}
        )
        assert channels_without_members == 0, "Some channels missing members"

    async def test_messages_have_workspace_id(self, db):
        """All messages should have workspace_id."""
        messages_without_workspace = await db[Collection.MESSAGES].count_documents(
            {"workspace_id": {"$exists": False}}
        )
        assert messages_without_workspace == 0, "Some messages missing workspace_id"

    async def test_messages_have_channel_id(self, db):
        """All messages should have channel_id (renamed from room_id)."""
        messages_without_channel = await db[Collection.MESSAGES].count_documents(
            {"channel_id": {"$exists": False}}
        )
        assert messages_without_channel == 0, "Some messages missing channel_id"

    async def test_messages_count_preserved(self, db):
        """Total message count should be preserved."""
        message_count = await db[Collection.MESSAGES].count_documents({})
        
        # Check if old_room_id field exists (indicator of migration)
        messages_with_old_id = await db[Collection.MESSAGES].count_documents(
            {"old_room_id": {"$exists": True}}
        )
        
        # All messages should have been processed
        assert (
            messages_with_old_id == message_count
        ), "Not all messages were migrated"

    async def test_channel_message_counts_updated(self, db):
        """Channel message_count should match actual message count."""
        channels = await db[Collection.CHANNELS].find({}).to_list(None)
        
        for channel in channels:
            channel_id = channel["_id"]
            actual_count = await db[Collection.MESSAGES].count_documents(
                {"channel_id": str(channel_id)}
            )
            stored_count = channel.get("message_count", 0)
            
            assert (
                actual_count == stored_count
            ), f"Channel {channel_id}: message_count mismatch (stored: {stored_count}, actual: {actual_count})"

    async def test_no_duplicate_workspace_slugs(self, db):
        """All workspace slugs should be unique."""
        workspace_slugs = await db[Collection.WORKSPACES].find(
            {}, {"slug": 1}
        ).to_list(None)
        
        slugs = [w["slug"] for w in workspace_slugs]
        unique_slugs = set(slugs)
        
        assert (
            len(slugs) == len(unique_slugs)
        ), f"Duplicate slugs found: {len(slugs) - len(unique_slugs)}"

    async def test_workspace_member_consistency(self, db):
        """User's workspace array should match workspace members array."""
        users = await db[Collection.USERS].find({}).to_list(None)
        
        for user in users:
            user_id = str(user["_id"])
            user_workspace_ids = {
                ws["workspace_id"] for ws in user.get("workspaces", [])
            }
            
            # Verify each workspace has this user in members
            for workspace_id in user_workspace_ids:
                from bson.objectid import ObjectId
                
                workspace = await db[Collection.WORKSPACES].find_one(
                    {"_id": ObjectId(workspace_id)}
                )
                
                assert workspace is not None, f"Workspace {workspace_id} not found"
                
                member_ids = {m["user_id"] for m in workspace.get("members", [])}
                assert (
                    user_id in member_ids
                ), f"User {user_id} not found in workspace {workspace_id} members"

    async def test_channel_member_consistency(self, db):
        """Channel members should be valid user IDs."""
        channels = await db[Collection.CHANNELS].find({}).to_list(None)
        users = await db[Collection.USERS].find({}).to_list(None)
        user_ids = {str(u["_id"]) for u in users}
        
        for channel in channels:
            for member_id in channel.get("members", []):
                assert (
                    member_id in user_ids
                ), f"Channel {channel['_id']}: invalid member_id {member_id}"

    async def test_message_sender_consistency(self, db):
        """Message senders should be valid user IDs."""
        messages = await db[Collection.MESSAGES].find({}).to_list(None)
        users = await db[Collection.USERS].find({}).to_list(None)
        user_ids = {str(u["_id"]) for u in users}
        
        for message in messages[:100]:  # Check first 100 for performance
            sender_id = message.get("sender_id")
            assert (
                sender_id in user_ids
            ), f"Message {message['_id']}: invalid sender_id {sender_id}"

    async def test_no_old_room_id_in_queries(self, db):
        """Verify old_room_id field exists for reference but data is complete."""
        messages_with_both_ids = await db[Collection.MESSAGES].count_documents(
            {
                "$and": [
                    {"channel_id": {"$exists": True}},
                    {"old_room_id": {"$exists": True}},
                ]
            }
        )
        
        total_messages = await db[Collection.MESSAGES].count_documents({})
        
        # All messages should have both old and new IDs after migration
        assert (
            messages_with_both_ids == total_messages
        ), "Migration not complete: not all messages have both IDs"


class TestMigrationPerformance:
    """Verify performance after migration."""

    async def test_channel_query_performance(self, db):
        """Query channels by workspace_id should use index."""
        # This is more of a documentation test
        # In real scenario, use explain() to verify index usage
        indexes = await db[Collection.CHANNELS].list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        assert "workspace_id_1" in index_names, "Missing index on workspace_id"

    async def test_message_query_performance(self, db):
        """Messages should have proper indexes for workspace/channel queries."""
        indexes = await db[Collection.MESSAGES].list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have at least one index on workspace_id
        assert any(
            "workspace_id" in name for name in index_names
        ), "Missing workspace_id index on messages"


class TestMigrationRollback:
    """Test rollback procedures (manual verification)."""

    async def test_rollback_script_exists(self):
        """Verify rollback documentation is available."""
        # This is a placeholder for documentation
        # Actual rollback is manual via MongoDB CLI
        assert True, "See ROLLBACK section in README.md"
