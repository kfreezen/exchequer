import json
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Query
import fastapi
from python_api.dependencies import UserRepositoryDep, RedisDep
from python_api.models import CamelModel
from python_api.models.users import (
    AdminUserViewModel,
)

from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["users"])


# Get all users
@router.get("", description="Get all users")
async def get_users(
    users: UserRepositoryDep,
    offset: int | None = None,
    limit: int | None = None,
    search: str | None = None,
):
    _users, total = await users.get_users(offset=offset, limit=limit, search=search)
    return {"data": _users, "total": total}


# Get user
@router.get("/{id}", description="Get user")
async def get_user(id: str, users: UserRepositoryDep):
    if user := await users.get_user(id):
        return user

    raise HTTPException(status_code=404, detail="User not found")


# Edit user
@router.put("/{id}", description="Edit user")
async def update_user(
    user: AdminUserViewModel,
    users: UserRepositoryDep,
    redis: RedisDep,
    _id: str = fastapi.Path(alias="id"),
    edit_subscription: bool = Query(default=False, alias="editSubscription"),
):
    # Update role in db
    db_user = await users.update_user(_id, user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user in Redis
    await redis.setex(
        f"users:{_id}", 2 * 60 * 60, json.dumps(jsonable_encoder(db_user))
    )

    if not edit_subscription:
        return


@router.put("/{id}/restrict", description="Restrict user")
async def restrict_user(
    users: UserRepositoryDep,
    redis: RedisDep,
    _id: str = fastapi.Path(alias="id"),
):
    await users.restrict_user(_id)
    user = await users.get_user(_id)

    # Update user in Redis
    await redis.setex(f"users:{_id}", 2 * 60 * 60, json.dumps(jsonable_encoder(user)))


@router.put("/{id}/un-restrict", description="Un-restrict user")
async def un_restrict_user(
    users: UserRepositoryDep,
    redis: RedisDep,
    _id: str = fastapi.Path(alias="id"),
):
    await users.un_restrict_user(_id)
    user = await users.get_user(_id)

    # Update user in Redis
    await redis.setex(f"users:{_id}", 2 * 60 * 60, json.dumps(jsonable_encoder(user)))
