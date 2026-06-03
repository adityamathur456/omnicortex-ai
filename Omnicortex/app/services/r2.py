from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class R2StorageError(RuntimeError):
    pass


class R2StorageService:
    def __init__(self) -> None:
        self._client = None

    @property
    def client(self):
        settings.require_r2()
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.r2_endpoint,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._client

    @staticmethod
    def _normalize_key(key: str) -> str:
        return str(PurePosixPath(key.strip().replace("\\", "/"))).lstrip("/")

    def generate_public_url(self, key: str) -> str:
        settings.require_r2()
        normalized = self._normalize_key(key)
        return f"{settings.r2_public_url.rstrip('/')}/{normalized}"

    def upload_bytes(self, file_bytes: bytes, key: str, content_type: str | None = None) -> str:
        settings.require_r2()
        normalized = self._normalize_key(key)
        guessed_type = content_type or mimetypes.guess_type(normalized)[0] or "application/octet-stream"
        try:
            self.client.put_object(
                Bucket=settings.r2_bucket_name,
                Key=normalized,
                Body=file_bytes,
                ContentType=guessed_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise R2StorageError(f"Failed to upload object to R2: {exc}") from exc
        return self.generate_public_url(normalized)


r2_storage_service = R2StorageService()
