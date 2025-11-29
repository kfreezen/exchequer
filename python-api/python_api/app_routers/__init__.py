from enum import Enum

from fastapi import APIRouter, Depends, Header, Query
import httpx
from pydantic import Field
from python_api.models import CamelModel

from python_api.dependencies import (
    SettingsDep,
    ValidJWTDep,
    requires_valid_subscription,
)

from . import bucket, users

app_router = APIRouter(
    prefix="",
    include_in_schema=True,
    dependencies=[],
)

authorized_router = APIRouter(
    prefix="",
    include_in_schema=True,
    dependencies=[
        Depends(requires_valid_subscription),
    ],
)


authorized_router.include_router(bucket.router)
authorized_router.include_router(users.router)
app_router.include_router(authorized_router)
