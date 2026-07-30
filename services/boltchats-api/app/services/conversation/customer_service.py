"""
Customer Service

Customer profile management and channel identities
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import Customer, CustomerIdentity
from app.repositories import CustomerIdentityRepository, CustomerRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class CustomerService(BaseService):
    """Manage customer profiles and channel identities"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.customers = CustomerRepository(db)
        self.identities = CustomerIdentityRepository(db)

    async def create_customer(
        self,
        org_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """
        Create new customer profile.
        
        Args:
            org_id: Organization ID
            name: Customer name
            email: Email address
            phone: Phone number
            
        Returns:
            Customer
        """
        customer = Customer(
            organization_id=org_id,
            name=name,
            email=email,
            phone=phone,
        )
        customer_id = await self.customers.create(customer)

        await self.log_action(
            "customer_created",
            resource_id=customer_id,
            resource_type="customer",
            details={"name": name},
        )

        return await self.customers.read(customer_id)

    async def get_customer(self, org_id: str, customer_id: str) -> Customer:
        """Get customer profile."""
        customer = await self.customers.read(customer_id)
        if not customer or customer.organization_id != org_id:
            raise NotFoundError("Customer", customer_id)
        return customer

    async def search_customers(
        self,
        org_id: str,
        query: str,
        limit: int = 20,
    ) -> list[Customer]:
        """
        Search customers by name, email, or phone.
        
        Args:
            org_id: Organization ID
            query: Search query
            limit: Max results
            
        Returns:
            List of customers
        """
        return await self.customers.search(org_id, query, limit)

    async def update_customer(
        self,
        org_id: str,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """Update customer profile."""
        customer = await self.get_customer(org_id, customer_id)

        from datetime import datetime, timezone
        update_data = {}
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if phone:
            update_data["phone"] = phone

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.customers.update(customer_id, update_data)
        return await self.customers.read(customer_id)

    # ─── CHANNEL IDENTITIES ────────────────────────────────────────────

    async def add_channel_identity(
        self,
        org_id: str,
        customer_id: str,
        provider: str,
        external_id: str,
        username: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CustomerIdentity:
        """
        Add channel identity to customer (Instagram, WhatsApp, Email, etc).
        
        One customer can have unlimited channel identities.
        Example: Ali has Instagram @ali34, WhatsApp +905551234567, Email ali@gmail.com
        
        Args:
            org_id: Organization ID
            customer_id: Customer ID
            provider: Provider name (instagram, whatsapp, email, facebook)
            external_id: Provider's ID (username, email, phone)
            username: Optional display username
            metadata: Provider-specific metadata
            
        Returns:
            CustomerIdentity
        """
        # Check customer exists
        customer = await self.get_customer(org_id, customer_id)

        # Check identity doesn't already exist for this provider
        existing = await self.identities.find_by_provider(customer_id, provider)
        if existing:
            raise ConflictError(
                f"Customer already has identity on {provider}"
            )

        # Create identity
        identity = CustomerIdentity(
            customer_id=customer_id,
            provider=provider,
            external_id=external_id,
            username=username,
            metadata=metadata or {},
        )
        identity_id = await self.identities.create(identity)

        await self.log_action(
            "channel_identity_added",
            resource_id=identity_id,
            resource_type="customer_identity",
            details={"provider": provider},
        )

        return await self.identities.read(identity_id)

    async def get_channel_identities(
        self,
        customer_id: str,
    ) -> list[CustomerIdentity]:
        """Get all channel identities for customer."""
        return await self.identities.find({"customer_id": customer_id})

    async def get_identity_by_provider(
        self,
        customer_id: str,
        provider: str,
    ) -> Optional[CustomerIdentity]:
        """Get specific channel identity."""
        return await self.identities.find_by_provider(customer_id, provider)

    async def update_channel_identity(
        self,
        org_id: str,
        customer_id: str,
        provider: str,
        metadata: Optional[dict] = None,
    ) -> CustomerIdentity:
        """Update channel identity metadata."""
        customer = await self.get_customer(org_id, customer_id)
        identity = await self.identities.find_by_provider(customer_id, provider)
        
        if not identity:
            raise NotFoundError("CustomerIdentity", f"{customer_id}:{provider}")

        from datetime import datetime, timezone
        update_data = {}
        if metadata:
            update_data["metadata"] = metadata
        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.identities.update(identity.id, update_data)
        return await self.identities.read(identity.id)

    async def remove_channel_identity(
        self,
        org_id: str,
        customer_id: str,
        provider: str,
    ) -> None:
        """Remove channel identity from customer."""
        customer = await self.get_customer(org_id, customer_id)
        identity = await self.identities.find_by_provider(customer_id, provider)
        
        if not identity:
            raise NotFoundError("CustomerIdentity", f"{customer_id}:{provider}")

        await self.identities.delete(identity.id)

        await self.log_action(
            "channel_identity_removed",
            resource_id=identity.id,
            resource_type="customer_identity",
            details={"provider": provider},
        )
