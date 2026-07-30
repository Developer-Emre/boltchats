"""
Password Service

Password hashing and verification using bcrypt
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """Handle password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plaintext password
            
        Returns:
            Hashed password (bcrypt format)
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plaintext: str, hashed: str) -> bool:
        """
        Verify plaintext password against hash.
        
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            plaintext: Plaintext password
            hashed: Bcrypt hash from database
            
        Returns:
            True if matches, False otherwise
        """
        return pwd_context.verify(plaintext, hashed)
