"""
Unit tests for Authentication Service

Tests: register, login, logout, password hashing, token management
All DB/Redis operations are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services import (
    AuthenticationService,
    PasswordService,
    TokenService,
    ValidationError,
    ConflictError,
)


@pytest.mark.asyncio
class TestPasswordService:
    """Password hashing and verification tests"""

    async def test_hash_password(self):
        """Test password hashing"""
        service = PasswordService()
        password = "test_password_123"

        hashed = await service.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    async def test_verify_password_success(self):
        """Test password verification - success"""
        service = PasswordService()
        password = "test_password_123"

        hashed = await service.hash_password(password)
        is_valid = await service.verify_password(password, hashed)

        assert is_valid is True

    async def test_verify_password_failure(self):
        """Test password verification - failure"""
        service = PasswordService()
        password = "test_password_123"
        wrong_password = "wrong_password_456"

        hashed = await service.hash_password(password)
        is_valid = await service.verify_password(wrong_password, hashed)

        assert is_valid is False


@pytest.mark.asyncio
class TestTokenService:
    """JWT token generation and validation tests"""

    async def test_create_access_token(self, user_id: str):
        """Test access token creation"""
        service = TokenService(MagicMock())
        
        token = service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_verify_token_success(self, user_id: str):
        """Test token verification - success"""
        service = TokenService(MagicMock())

        token = service.create_access_token(user_id)
        decoded = service.verify_token(token)

        assert decoded is not None
        assert decoded["user_id"] == user_id

    async def test_verify_token_invalid(self):
        """Test token verification - invalid token"""
        service = TokenService(MagicMock())

        with pytest.raises(Exception):
            service.verify_token("invalid.token.here")

    async def test_create_refresh_token(self, user_id: str):
        """Test refresh token creation"""
        service = TokenService(MagicMock())

        token = service.create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)


@pytest.mark.asyncio
class TestAuthenticationService:
    """User registration and login tests"""

    async def test_register_success(
        self,
        mock_db: MagicMock,
        org_id: str,
        test_user_data: dict,
    ):
        """Test user registration - success"""
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)  # Email not in use
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=test_user_data["id"]))
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        service = AuthenticationService(mock_db, MagicMock())

        result = await service.register(
            email=test_user_data["email"],
            password="test_password_123",
            full_name=test_user_data["full_name"],
            organization_name="Test Org",
        )

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

    async def test_register_email_already_exists(
        self,
        mock_db: MagicMock,
        test_user_data: dict,
    ):
        """Test user registration - email already exists"""
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=test_user_data)  # Email exists
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        service = AuthenticationService(mock_db, MagicMock())

        with pytest.raises(ConflictError):
            await service.register(
                email=test_user_data["email"],
                password="test_password_123",
                full_name=test_user_data["full_name"],
                organization_name="Test Org",
            )

    async def test_login_success(
        self,
        mock_db: MagicMock,
        test_user_data: dict,
    ):
        """Test user login - success"""
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=test_user_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        service = AuthenticationService(mock_db, MagicMock())
        password_service = PasswordService()

        # Create properly hashed password
        hashed = await password_service.hash_password("test_password_123")
        test_user_data["password_hash"] = hashed

        result = await service.login(
            email=test_user_data["email"],
            password="test_password_123",
        )

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result

    async def test_login_user_not_found(self, mock_db: MagicMock):
        """Test user login - user not found"""
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        service = AuthenticationService(mock_db, MagicMock())

        with pytest.raises(Exception):
            await service.login(
                email="nonexistent@example.com",
                password="test_password_123",
            )

    async def test_login_wrong_password(
        self,
        mock_db: MagicMock,
        test_user_data: dict,
    ):
        """Test user login - wrong password"""
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=test_user_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        service = AuthenticationService(mock_db, MagicMock())

        with pytest.raises(Exception):
            await service.login(
                email=test_user_data["email"],
                password="wrong_password_456",
            )
