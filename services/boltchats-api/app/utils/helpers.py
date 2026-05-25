from bson import ObjectId
from bson.errors import InvalidId

from app.exceptions.http_exceptions import NotFoundException
from app.utils.constants import ErrorMessage


def parse_object_id(value: str, detail: str = ErrorMessage.INVALID_ID) -> ObjectId:
    """Parse a string to ObjectId, raising NotFoundException on invalid input."""
    try:
        return ObjectId(value)
    except InvalidId:
        raise NotFoundException(detail)
