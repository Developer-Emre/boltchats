"""
ULID (Universally Unique Lexicographically Sortable Identifier) utility

ULID provides:
- Time-sortable IDs (unlike UUID)
- Distributed safety (like UUID)
- Readable format (unlike MongoDB ObjectId)
- Portable (database agnostic)
"""

from ulid import ULID as _ULID
from typing import Dict


# ULID prefixes for different entity types
PREFIXES: Dict[str, str] = {
    "organization": "org",
    "workspace": "ws",
    "team": "team",
    "member": "mem",
    "user": "usr",
    "customer": "cust",
    "customer_identity": "custid",
    "conversation": "conv",
    "conversation_participant": "convpart",
    "message": "msg",
    "draft": "draft",
    "label": "lbl",
    "integration": "int",
    "event": "evt",
    "audit_log": "audit",
    "notification": "notif",
    "role": "role",
    "permission": "perm",
    "invitation": "inv",
    "webhook_delivery": "webhook",
    "refresh_token": "refresh",
}


def generate_ulid(prefix: str) -> str:
    """
    Generate a ULID with entity-specific prefix.

    Args:
        prefix: Entity type prefix (organization, member, etc.)

    Returns:
        ULID string with prefix (e.g., org_01K3F7M5Q9H6X)

    Raises:
        ValueError: If prefix is not recognized
    """
    if prefix not in PREFIXES:
        raise ValueError(f"Unknown prefix: {prefix}. Valid prefixes: {list(PREFIXES.keys())}")

    ulid_part = str(_ULID())
    prefix_part = PREFIXES[prefix]
    return f"{prefix_part}_{ulid_part}"


def generate_ulid_raw() -> str:
    """Generate raw ULID without prefix"""
    return str(_ULID())


def parse_ulid(ulid_str: str) -> tuple[str, str] | None:
    """
    Parse ULID string to extract prefix and ID.

    Args:
        ulid_str: ULID string (e.g., org_01K3F7M5Q9H6X)

    Returns:
        Tuple of (prefix, ulid_part) or None if invalid
    """
    if not ulid_str or "_" not in ulid_str:
        return None

    try:
        prefix, ulid_part = ulid_str.split("_", 1)
        return prefix, ulid_part
    except ValueError:
        return None


def is_valid_ulid(ulid_str: str) -> bool:
    """
    Validate ULID format.

    Args:
        ulid_str: ULID string to validate

    Returns:
        True if valid ULID format
    """
    if not ulid_str or "_" not in ulid_str:
        return False

    try:
        prefix, ulid_part = ulid_str.split("_", 1)
        # Validate prefix exists
        if prefix not in PREFIXES.values():
            return False
        # Validate ULID part
        _ULID.from_str(ulid_part)
        return True
    except (ValueError, TypeError):
        return False


# Entity ID generators (convenience functions)
def new_organization_id() -> str:
    return generate_ulid("organization")


def new_workspace_id() -> str:
    return generate_ulid("workspace")


def new_member_id() -> str:
    return generate_ulid("member")


def new_user_id() -> str:
    return generate_ulid("user")


def new_customer_id() -> str:
    return generate_ulid("customer")


def new_conversation_id() -> str:
    return generate_ulid("conversation")


def new_message_id() -> str:
    return generate_ulid("message")


def new_integration_id() -> str:
    return generate_ulid("integration")


def new_event_id() -> str:
    return generate_ulid("event")


def new_notification_id() -> str:
    return generate_ulid("notification")


def new_role_id() -> str:
    return generate_ulid("role")


def new_team_id() -> str:
    return generate_ulid("team")
