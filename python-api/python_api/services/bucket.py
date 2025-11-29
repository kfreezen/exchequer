import os
from typing import Annotated, Literal
import uuid
from fastapi import File, UploadFile

import pathlib
import io

import starlette

from python_api.Error import FileNotFoundException
from PIL import Image

SupportedUploads = Literal["attachments"]
SupportedDownloads = Literal["attachments"]


class FileBucket:
    def __init__(self, bucket_storage: str):
        self.bucket_path = pathlib.Path(bucket_storage)

    async def upload_file(
        self,
        bucket: SupportedUploads,
        file: Annotated[
            UploadFile | io.BytesIO | bytes, File(description="Upload Contract PDF")
        ],
        file_key: str,
        is_byte_stream: bool = False,
    ):
        file_key = str(uuid.uuid4())
        file_path = self.bucket_path / bucket / (file_key + ".pdf")

        with file_path.open("wb") as uploaded:
            if isinstance(file, bytes):
                uploaded.write(file)
            elif is_byte_stream:
                if isinstance(file, io.BytesIO):
                    uploaded.write(file.read())
                else:
                    uploaded.write(await file.read())
            else:
                if hasattr(file, "file"):
                    uploaded.write(file.file.read())  # pyright: ignore
                else:
                    uploaded.write(file.read())  # pyright: ignore

        return file_key

    async def upload_cover(
        self,
        bucket: Literal["covers"],
        file: Annotated[UploadFile, File(description="Cover File")],
        file_key: str,
    ) -> str:
        file_path: pathlib.Path = self.bucket_path / bucket / file_key
        with file_path.open("wb") as uploaded:
            uploaded.write(file.file.read())

        # Resize the cover image
        image = Image.open(file_path)
        image.thumbnail((508, 660))

        if image.mode == "RGBA":
            image = image.convert("RGB")

        key, _ = os.path.splitext(file_key)
        file_key = key + "-thumb.jpg"
        file_path = self.bucket_path / bucket / file_key
        image.save(file_path)

        return file_key

    async def get_bucket_file(
        self,
        _key: str,
        bucket: SupportedDownloads,
    ) -> str:
        file_key = self.bucket_path / bucket / _key

        if not file_key.exists():
            raise FileNotFoundException(err_message="File {} not found".format(_key))

        return str(file_key)

    def get_bucket_path(
        self,
        bucket: SupportedDownloads,
    ) -> pathlib.Path:
        return self.bucket_path / bucket

    def get_bucket_file_stream(self, file_key: str) -> io.BytesIO:
        with open(file_key, "rb") as file:
            return io.BytesIO(file.read())

    async def delete_bucket_file(self, _key: str, bucket: SupportedUploads):
        if _key:
            file_key = await self.get_bucket_file(_key=_key, bucket=bucket)
            pathlib.Path(file_key).unlink()
