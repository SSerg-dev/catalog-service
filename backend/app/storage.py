from functools import partial
from io import BytesIO
from typing import Iterator

from anyio import to_thread
from minio import Minio

from app.config import settings


class ObjectStorage:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        operation = partial(
            self._client.put_object,
            settings.minio_bucket,
            key,
            BytesIO(content),
            len(content),
            content_type=content_type,
        )
        await to_thread.run_sync(operation)

    async def delete(self, key: str) -> None:
        await to_thread.run_sync(self._client.remove_object, settings.minio_bucket, key)

    async def open(self, key: str):
        return await to_thread.run_sync(self._client.get_object, settings.minio_bucket, key)

    @staticmethod
    def chunks(response, size: int = 64 * 1024) -> Iterator[bytes]:
        try:
            while chunk := response.read(size):
                yield chunk
        finally:
            response.close()
            response.release_conn()


storage = ObjectStorage()

