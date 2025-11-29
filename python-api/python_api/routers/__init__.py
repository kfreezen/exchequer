from fastapi import APIRouter, Depends
from python_api import dependencies


admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(dependencies.admin)],
)
