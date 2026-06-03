from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip('"').strip("'").strip()


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    cloudflare_account_id: str | None = _env("CLOUDFLARE_ACCOUNT_ID")
    cloudflare_workers_auth_token: str | None = _env("CLOUDFLARE_WORKERS_AUTH_TOKEN")
    cloudflare_google_imagen_api_token: str | None = _env("CLOUDFLARE_GOOGLE_IMAGEN_API_TOKEN")
    cloudflare_imagen_proxy_url: str | None = _env("CLOUDFLARE_IMAGEN_PROXY_URL")
    imagen_proxy_auth_token: str | None = _env("IMAGEN_PROXY_AUTH_TOKEN")
    cloudflare_r2_auth_token: str | None = _env("CLOUDFLAR_R2_AUTH_TOKEN")

    r2_bucket_name: str | None = _env("R2_BUCKET_NAME")
    r2_access_key_id: str | None = _env("R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = _env("R2_SECRET_ACCESS_KEY")
    r2_endpoint: str | None = _env("R2_ENDPOINT")
    r2_public_url: str | None = _env("R2_PUBLIC_URL")

    jwt_secret_key: str | None = _env("JWT_SECRET_KEY")
    jwt_algorithm: str = _env("JWT_ALGORITHM", "HS256") or "HS256"
    jwt_expire_minutes: int = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)
    auth_backend: str = _env("AUTH_BACKEND", "") or ""
    postgres_dsn: str | None = _env("POSTGRES_DSN")
    d1_database_id: str | None = _env("D1_DATABASE_ID")
    d1_api_token: str | None = _env("D1_API_TOKEN")

    workers_text_model: str = (
        _env("WORKERS_TEXT_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
        or "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    )
    workers_medical_model: str = (
        _env("WORKERS_MEDICAL_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
        or "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    )
    workers_medical_vision_model: str = (
        _env("WORKERS_MEDICAL_VISION_MODEL", "@cf/meta/llama-3.2-11b-vision-instruct")
        or "@cf/meta/llama-3.2-11b-vision-instruct"
    )
    workers_embedding_model: str = (
        _env("WORKERS_EMBEDDING_MODEL", "@cf/baai/bge-base-en-v1.5")
        or "@cf/baai/bge-base-en-v1.5"
    )
    workers_image_model: str = (
        _env("WORKERS_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
        or "@cf/black-forest-labs/flux-1-schnell"
    )
    cloudflare_ai_gateway_id: str = _env("CLOUDFLARE_AI_GATEWAY_ID", "default") or "default"
    latex_engine: str = _env("LATEX_ENGINE", "xelatex") or "xelatex"
    latex_timeout_seconds: int = _env_int("LATEX_TIMEOUT_SECONDS", 180)
    latex_compiler_service_url: str | None = _env("LATEX_COMPILER_SERVICE_URL")
    latex_compiler_service_token: str | None = _env("LATEX_COMPILER_SERVICE_TOKEN")
    latex_compiler_service_timeout_seconds: int = _env_int("LATEX_COMPILER_SERVICE_TIMEOUT_SECONDS", 180)

    storage_dir: Path = BASE_DIR / "storage"
    vector_store_path: Path = BASE_DIR / "storage" / "vector_store.json"
    auth_db_path: Path = BASE_DIR / "storage" / "auth.db"
    generated_dir: Path = BASE_DIR / "storage" / "generated"

    resume_dirs: tuple[Path, ...] = (BASE_DIR / "data" / "resumes", BASE_DIR / "resumes")
    chunk_size: int = _env_int("RAG_CHUNK_SIZE", 1100)
    chunk_overlap: int = _env_int("RAG_CHUNK_OVERLAP", 180)
    rag_top_k: int = _env_int("RAG_TOP_K", 5)

    cors_origins: tuple[str, ...] = ("*",)

    def ensure_runtime_dirs(self) -> None:
        for path in (self.storage_dir, self.generated_dir):
            path.mkdir(parents=True, exist_ok=True)

    def require_workers_ai(self) -> None:
        missing = [
            name
            for name, value in (
                ("CLOUDFLARE_ACCOUNT_ID", self.cloudflare_account_id),
                ("CLOUDFLARE_WORKERS_AUTH_TOKEN", self.cloudflare_workers_auth_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required Workers AI environment variables: {', '.join(missing)}")

    def require_imagen_ai(self) -> None:
        if self.cloudflare_imagen_proxy_url:
            return
        missing = [
            name
            for name, value in (
                ("CLOUDFLARE_ACCOUNT_ID", self.cloudflare_account_id),
                ("CLOUDFLARE_GOOGLE_IMAGEN_API_TOKEN", self.cloudflare_google_imagen_api_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required Google Imagen environment variables: {', '.join(missing)}")

    def require_r2(self) -> None:
        missing = [
            name
            for name, value in (
                ("R2_BUCKET_NAME", self.r2_bucket_name),
                ("R2_ACCESS_KEY_ID", self.r2_access_key_id),
                ("R2_SECRET_ACCESS_KEY", self.r2_secret_access_key),
                ("R2_ENDPOINT", self.r2_endpoint),
                ("R2_PUBLIC_URL", self.r2_public_url),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required R2 environment variables: {', '.join(missing)}")

    def require_auth(self) -> None:
        if not self.jwt_secret_key:
            raise RuntimeError("Missing required JWT_SECRET_KEY environment variable")
        if len(self.jwt_secret_key.encode("utf-8")) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes long")

    def selected_auth_backend(self) -> str:
        if self.auth_backend:
            return self.auth_backend.lower()
        if self.postgres_dsn:
            return "postgres"
        if self.d1_database_id and self.d1_api_token:
            return "d1"
        return "sqlite"

    def require_postgres_auth(self) -> None:
        if not self.postgres_dsn:
            raise RuntimeError("Missing required POSTGRES_DSN environment variable")

    def require_d1_auth(self) -> None:
        missing = [
            name
            for name, value in (
                ("CLOUDFLARE_ACCOUNT_ID", self.cloudflare_account_id),
                ("D1_DATABASE_ID", self.d1_database_id),
                ("D1_API_TOKEN", self.d1_api_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required D1 auth environment variables: {', '.join(missing)}")

    def existing_resume_dirs(self) -> Iterable[Path]:
        return (path for path in self.resume_dirs if path.exists())


settings = Settings()
