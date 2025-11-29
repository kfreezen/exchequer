import asyncio
import mimetypes
import time
from typing import Annotated, Literal
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from python_api import dependencies
from python_api.services.bucket import SupportedDownloads

router = APIRouter(prefix="/bucket", tags=["bucket"])


@router.post(
    "/covers", dependencies=[Depends(dependencies.requires_valid_subscription)]
)
async def upload_cover(
    file: Annotated[UploadFile, File(description="Cover File")],
    bucket_store: dependencies.BucketStorageDep,
):
    if not file.content_type and not file.filename:
        raise HTTPException(
            400, detail="Cover File doesn't have content-type or filename attached"
        )
    elif not file.filename:
        extension = mimetypes.guess_extension(file.content_type or "")
        if not extension:
            raise HTTPException(
                400, detail="Could not guess file extension from content type"
            )

        file_key = str(uuid.uuid4()) + extension
    else:
        file_key = file.filename

    file_key = await bucket_store.upload_cover(
        bucket="covers", file=file, file_key=file_key
    )

    return {"fileKey": file_key}


@router.get("/covers/{_key}", description="Get cover file.")
async def get_cover_file(
    _key: str,
    bucket_store: dependencies.BucketStorageDep,
):
    guessed_type = mimetypes.guess_type(_key)
    file_key = await bucket_store.get_bucket_file(_key=_key, bucket="covers")

    return FileResponse(file_key, media_type=guessed_type[0] or "application/pdf")


@router.get(
    "/{bucket}/{_key}",
    description="Get file from key.",
    dependencies=[Depends(dependencies.requires_valid_subscription)],
)
async def get_bucket_file(
    bucket: Literal["attachments"],
    _key: str,
    bucket_store: dependencies.BucketStorageDep,
    valid_jwt: dependencies.ValidJWTDep,
    redis: dependencies.RedisDep,
):
    guessed_type = mimetypes.guess_type(_key)
    file_key = await bucket_store.get_bucket_file(_key=_key, bucket=bucket)

    return FileResponse(file_key, media_type=guessed_type[0] or "application/pdf")


# Check if file exists
@router.get("/{bucket}/{_key}/exists", description="Check if file exists.")
async def check_file_exists(
    bucket: SupportedDownloads,
    _key: str,
    bucket_store: dependencies.BucketStorageDep,
):
    try:
        await bucket_store.get_bucket_file(_key=_key, bucket=bucket)
    except Exception:
        return False

    return True


@router.delete(
    "/{bucket}/{_key}",
    description="Delete file by key.",
    dependencies=[Depends(dependencies.admin)],
)
async def delete_bucket_file(
    bucket: Literal["attachments"],
    _key: str,
    bucket_store: dependencies.BucketStorageDep,
):
    await bucket_store.delete_bucket_file(_key=_key, bucket=bucket)
