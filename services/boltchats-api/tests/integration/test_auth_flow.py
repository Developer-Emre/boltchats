"""
Integration tests for authentication flow

Tests: Registration, login, JWT validation, token refresh
"""

import pytest
from datetime import datetime, timezone

from app.services import AuthenticationService, PasswordService, TokenService
from app.core.config import Settings
from app.schemas import UserRegisterRequest, UserLoginRequest


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """End-to-end authentication flow tests"""

    async def test_user_registration_and_login_flow(
        self,
        mongodb,
        settings: Settings,
    ):
        """Test complete registration and login flow"""
        auth_service = AuthenticationService(mongodb)
        password_service = PasswordService()

        # Step 1: Register user
        register_data = UserRegisterRequest(
            email="integration@test.com",
            password="SecurePassword123!",
            first_name="Integration",
            last_name="Test",
        )

        user = await auth_service.register(
            email=register_data.email,
            password=register_data.password,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
        )

        assert user is not None
        assert user["email"] == register_data.email
        assert "password_hash" in user
        assert user["status"] == "active"

        # Verify password was hashed
        assert password_service.verify(
            register_data.password,
            user["password_hash"],
        )

        # Step 2: Login with same credentials
        login_data = UserLoginRequest(
            email=register_data.email,
            password=register_data.password,
        )

        authenticated_user = await auth_service.authenticate(
            email=login_data.email,
            password=login_data.password,
        )

        assert authenticated_user is not None
        assert authenticated_user["email"] == register_data.email

    async def test_token_generation_and_validation(
        self,
        settings: Settings,
    ):
        """Test JWT token generation and validation"""
        token_service = TokenService(settings)

        user_id = "user-int-test-123"
        org_id = "org-int-test-456"

        # Generate tokens
        access_token = token_service.encode_access_token(
            user_id=user_id,
            org_id=org_id,
        )
        refresh_token = token_service.encode_refresh_token(
            user_id=user_id,
        )

        assert access_token is not None
        assert refresh_token is not None

        # Validate access token
        decoded_access = token_service.decode_access_token(access_token)
        assert decoded_access is not None
        assert decoded_access["user_id"] == user_id
        assert decoded_access["org_id"] == org_id

        # Validate refresh token
        decoded_refresh = token_service.decode_refresh_token(refresh_token)
        assert decoded_refresh is not None
        assert decoded_refresh["user_id"] == user_id

    async def test_expired_token_validation(
        self,
        settings: Settings,
    ):
        """Test that expired tokens are rejected"""
        token_service = TokenService(settings)

        user_id = "user-exp-test"

        # Create an already-expired token by mocking the expiry
        expired_token = token_service.encode_access_token(
            user_id=user_id,
            org_id="org-test",
            expires_in=-1,  # Already expired
        )

        # Decoding should return None for expired token
        decoded = token_service.decode_access_token(expired_token)
        assert decoded is None or "error" in decoded

    async def test_password_reset_flow(
        self,
        mongodb,
    ):
        """Test password reset flow"""
        auth_service = AuthenticationService(mongodb)
        password_service = PasswordService()

        # Register user first
        user = await auth_service.register(
            email="reset@test.com",
            password="OldPassword123!",
            first_name="Reset",
            last_name="Test",
        )

        old_hash = user["password_hash"]

        # Reset password
        new_password = "NewPassword456!"
        await auth_service.change_password(
            user_id=user["id"],
            old_password="OldPassword123!",
            new_password=new_password,
        )

        # Fetch updated user
        updated_user = await mongodb["users"].find_one({"_id": user["id"]})

        # Verify password was changed
        assert password_service.verify(new_password, updated_user["password_hash"])
        assert old_hash != updated_user["password_hash"]

    async def test_duplicate_email_registration(
        self,
        mongodb,
    ):
        """Test registration with duplicate email"""
        auth_service = AuthenticationService(mongodb)

        # First registration
        await auth_service.register(
            email="duplicate@test.com",
            password="Password123!",
            first_name="First",
            last_name="User",
        )

        # Second registration with same email should fail
        with pytest.raises(Exception):  # ValidationError
            await auth_service.register(
                email="duplicate@test.com",
                password="Password456!",
                first_name="Second",
                last_name="User",
            )

    async def test_invalid_password_login(
        self,
        mongodb,
    ):
        """Test login with invalid password"""
        auth_service = AuthenticationService(mongodb)

        # Register user
        await auth_service.register(
            email="invalid@test.com",
            password="CorrectPassword123!",
            first_name="Invalid",
            last_name="Test",
        )

        # Try to login with wrong password
        result = await auth_service.authenticate(
            email="invalid@test.com",
            password="WrongPassword456!",
        )

        assert result is None
