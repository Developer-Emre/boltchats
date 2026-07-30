"""
Base Repository Pattern for MongoDB with Motor

Generic CRUD operations for all domain models.
"""

from typing import Any, Generic, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, model_class: Type[T]):
        self.db = db
        self.collection: AsyncIOMotorCollection = db[collection_name]
        self.model_class = model_class

    async def create(self, document: T) -> str:
        """Create a new document.
        
        Args:
            document: Pydantic model instance
            
        Returns:
            Inserted document ID
        """
        doc_dict = document.model_dump(by_alias=True, exclude_none=False)
        result = await self.collection.insert_one(doc_dict)
        return str(result.inserted_id)

    async def read(self, document_id: str) -> T | None:
        """Read a document by ID.
        
        Args:
            document_id: MongoDB ObjectId as string
            
        Returns:
            Model instance or None if not found
        """
        from bson import ObjectId

        try:
            doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            if doc:
                return self.model_class.model_validate(doc)
            return None
        except Exception:
            return None

    async def update(self, document_id: str, update_data: dict) -> bool:
        """Update a document.
        
        Args:
            document_id: MongoDB ObjectId as string
            update_data: Fields to update
            
        Returns:
            True if updated, False otherwise
        """
        from bson import ObjectId

        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def delete(self, document_id: str) -> bool:
        """Delete a document (soft delete if has deleted_at field).
        
        Args:
            document_id: MongoDB ObjectId as string
            
        Returns:
            True if deleted, False otherwise
        """
        from bson import ObjectId
        from datetime import datetime, timezone

        try:
            # Try soft delete first (if model has deleted_at)
            doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            if doc and "deleted_at" in doc:
                result = await self.collection.update_one(
                    {"_id": ObjectId(document_id)},
                    {"$set": {"deleted_at": datetime.now(timezone.utc)}}
                )
                return result.modified_count > 0
            
            # Otherwise hard delete
            result = await self.collection.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def find(self, filter_dict: dict) -> T | None:
        """Find a single document by filter.
        
        Args:
            filter_dict: MongoDB filter query
            
        Returns:
            Model instance or None if not found
        """
        doc = await self.collection.find_one(filter_dict)
        if doc:
            return self.model_class.model_validate(doc)
        return None

    async def find_many(self, filter_dict: dict, skip: int = 0, limit: int = 100) -> list[T]:
        """Find multiple documents.
        
        Args:
            filter_dict: MongoDB filter query
            skip: Number of documents to skip
            limit: Maximum documents to return
            
        Returns:
            List of model instances
        """
        cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model_class.model_validate(doc) for doc in docs]

    async def count(self, filter_dict: dict = None) -> int:
        """Count documents matching filter.
        
        Args:
            filter_dict: MongoDB filter query (optional)
            
        Returns:
            Number of matching documents
        """
        if filter_dict is None:
            filter_dict = {}
        return await self.collection.count_documents(filter_dict)

    async def exists(self, filter_dict: dict) -> bool:
        """Check if document exists.
        
        Args:
            filter_dict: MongoDB filter query
            
        Returns:
            True if document exists
        """
        return await self.collection.count_documents(filter_dict) > 0

    async def delete_many(self, filter_dict: dict) -> int:
        """Delete multiple documents.
        
        Args:
            filter_dict: MongoDB filter query
            
        Returns:
            Number of deleted documents
        """
        result = await self.collection.delete_many(filter_dict)
        return result.deleted_count

    async def update_many(self, filter_dict: dict, update_data: dict) -> int:
        """Update multiple documents.
        
        Args:
            filter_dict: MongoDB filter query
            update_data: Fields to update
            
        Returns:
            Number of updated documents
        """
        result = await self.collection.update_many(
            filter_dict,
            {"$set": update_data}
        )
        return result.modified_count

    async def create_index(self, keys: list[tuple[str, int]] | str, unique: bool = False) -> str:
        """Create an index on the collection.
        
        Args:
            keys: Index key specification
            unique: Whether index should be unique
            
        Returns:
            Index name
        """
        return await self.collection.create_index(keys, unique=unique)

    async def drop_index(self, index_name: str) -> None:
        """Drop an index.
        
        Args:
            index_name: Name of index to drop
        """
        await self.collection.drop_index(index_name)

    async def list_indexes(self) -> list[dict]:
        """List all indexes on collection.
        
        Returns:
            List of index specifications
        """
        async for index_info in self.collection.list_indexes():
            yield index_info
