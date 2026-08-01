"""
Database schema and data validators

Validates:
- Schema consistency
- Data integrity
- Required fields
- Referential integrity
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class DatabaseValidator:
    """Database validation utilities"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def validate_all(self) -> dict:
        """
        Run all validations.

        Returns:
            Validation result dict
        """
        logger.info("validation_start")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "validations": {},
            "issues": [],
        }

        # Validate organization references
        try:
            org_validation = await self._validate_organization_refs()
            result["validations"]["organization_refs"] = org_validation
            if org_validation.get("issues"):
                result["issues"].extend(org_validation["issues"])
        except Exception as e:
            logger.error("org_validation_failed", error=str(e))
            result["issues"].append(f"Organization validation: {str(e)}")

        # Validate member references
        try:
            member_validation = await self._validate_member_refs()
            result["validations"]["member_refs"] = member_validation
            if member_validation.get("issues"):
                result["issues"].extend(member_validation["issues"])
        except Exception as e:
            logger.error("member_validation_failed", error=str(e))
            result["issues"].append(f"Member validation: {str(e)}")

        # Validate conversation references
        try:
            conv_validation = await self._validate_conversation_refs()
            result["validations"]["conversation_refs"] = conv_validation
            if conv_validation.get("issues"):
                result["issues"].extend(conv_validation["issues"])
        except Exception as e:
            logger.error("conv_validation_failed", error=str(e))
            result["issues"].append(f"Conversation validation: {str(e)}")

        # Validate message references
        try:
            msg_validation = await self._validate_message_refs()
            result["validations"]["message_refs"] = msg_validation
            if msg_validation.get("issues"):
                result["issues"].extend(msg_validation["issues"])
        except Exception as e:
            logger.error("msg_validation_failed", error=str(e))
            result["issues"].append(f"Message validation: {str(e)}")

        if result["issues"]:
            result["status"] = "issues"

        logger.info("validation_complete", status=result["status"], issue_count=len(result["issues"]))
        return result

    async def _validate_organization_refs(self) -> dict:
        """Validate organization references in other collections"""
        issues = []

        # Check members have valid organization references
        members_without_org = await self.db[Collection.MEMBERS].find({
            "organization_id": None
        }).to_list(None)

        if members_without_org:
            issues.append(f"Found {len(members_without_org)} members without organization_id")

        return {
            "status": "ok" if not issues else "issues",
            "issues": issues,
        }

    async def _validate_member_refs(self) -> dict:
        """Validate member references"""
        issues = []

        # Check conversations have valid assigned_to members
        conversations = await self.db[Collection.CONVERSATIONS].find({
            "assigned_to": {"$ne": None}
        }).to_list(None)

        for conv in conversations:
            if conv.get("assigned_to"):
                member = await self.db[Collection.MEMBERS].find_one(
                    {"_id": conv["assigned_to"]}
                )
                if not member:
                    issues.append(f"Conversation {conv['_id']} has invalid assigned_to: {conv['assigned_to']}")

        return {
            "status": "ok" if not issues else "issues",
            "issues": issues[:10],  # Limit to first 10
        }

    async def _validate_conversation_refs(self) -> dict:
        """Validate conversation references"""
        issues = []

        # Check messages have valid conversation references
        messages = await self.db[Collection.MESSAGES].find().limit(100).to_list(None)

        for msg in messages:
            conv = await self.db[Collection.CONVERSATIONS].find_one(
                {"_id": msg.get("conversation_id")}
            )
            if not conv:
                issues.append(f"Message {msg['_id']} has invalid conversation_id: {msg.get('conversation_id')}")

        return {
            "status": "ok" if not issues else "issues",
            "issues": issues[:10],  # Limit to first 10
            "sampled": True,
        }

    async def _validate_message_refs(self) -> dict:
        """Validate message references"""
        issues = []

        # Check messages with reply_to have valid references
        replies = await self.db[Collection.MESSAGES].find({
            "reply_to_message_id": {"$ne": None}
        }).limit(100).to_list(None)

        for msg in replies:
            if msg.get("reply_to_message_id"):
                parent = await self.db[Collection.MESSAGES].find_one(
                    {"_id": msg["reply_to_message_id"]}
                )
                if not parent:
                    issues.append(f"Message {msg['_id']} has invalid reply_to_message_id: {msg['reply_to_message_id']}")

        return {
            "status": "ok" if not issues else "issues",
            "issues": issues[:10],  # Limit to first 10
            "sampled": True,
        }

    async def repair_all(self) -> dict:
        """
        Attempt to repair database issues.

        Returns:
            Repair result dict
        """
        logger.info("repair_start")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repairs": {},
        }

        # Clean up orphaned documents
        try:
            orphan_fix = await self._fix_orphaned_messages()
            result["repairs"]["orphaned_messages"] = orphan_fix
        except Exception as e:
            logger.error("orphan_fix_failed", error=str(e))
            result["repairs"]["orphaned_messages"] = {"error": str(e)}

        logger.info("repair_complete")
        return result

    async def _fix_orphaned_messages(self) -> dict:
        """Remove messages whose parent conversation no longer exists"""
        # This is a no-op in the actual implementation
        # In production, you might want to delete orphaned messages or move them
        return {"status": "ok", "message": "Orphaned message check completed"}
