from fastapi import APIRouter, Depends

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.user_schema import UpdateUserRequest, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> UserResponse:
    return await user_service.get_me(user_id, db)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateUserRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> UserResponse:
    return await user_service.update_me(user_id, payload, db)


@router.get("/{target_id}", response_model=UserResponse)
async def get_user(
    target_id: str,
    _current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> UserResponse:
    return await user_service.get_by_id(target_id, db)
