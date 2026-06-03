from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Protocol

import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.utils.security import create_access_token, hash_password, verify_password


@dataclass(frozen=True)
class AuthUser:
    id: int
    email: str
    full_name: str | None


class AuthBackend(Protocol):
    def initialize(self) -> None: ...

    def register(self, email: str, password_hash: str, full_name: str | None = None) -> AuthUser: ...

    def authenticate(self, email: str, password: str) -> str: ...

    def get_user_by_id(self, user_id: str) -> AuthUser: ...


class SQLiteAuthBackend:
    def __init__(self) -> None:
        self.db_path = settings.auth_db_path

    def initialize(self) -> None:
        settings.ensure_runtime_dirs()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def register(self, email: str, password_hash: str, full_name: str | None = None) -> AuthUser:
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, full_name, password_hash) VALUES (?, ?, ?)",
                    (email, full_name, password_hash),
                )
                conn.commit()
                user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
        return AuthUser(id=user_id, email=email, full_name=full_name)

    def authenticate(self, email: str, password: str) -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return create_access_token(subject=str(row["id"]), extra_claims={"email": row["email"]})

    def get_user_by_id(self, user_id: str) -> AuthUser:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, full_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return AuthUser(id=int(row["id"]), email=row["email"], full_name=row["full_name"])


class PostgresAuthBackend:
    def __init__(self) -> None:
        settings.require_postgres_auth()
        self.dsn = settings.postgres_dsn

    @staticmethod
    def _psycopg():
        import psycopg

        return psycopg

    def initialize(self) -> None:
        psycopg = self._psycopg()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        full_name TEXT,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            conn.commit()

    def register(self, email: str, password_hash: str, full_name: str | None = None) -> AuthUser:
        psycopg = self._psycopg()
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO users (email, full_name, password_hash)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (email, full_name, password_hash),
                    )
                    user_id = int(cur.fetchone()[0])
                conn.commit()
        except psycopg.errors.UniqueViolation as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
        return AuthUser(id=user_id, email=email, full_name=full_name)

    def authenticate(self, email: str, password: str) -> str:
        psycopg = self._psycopg()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, password_hash FROM users WHERE email = %s",
                    (email,),
                )
                row = cur.fetchone()
        if row is None or not verify_password(password, row[2]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return create_access_token(subject=str(row[0]), extra_claims={"email": row[1]})

    def get_user_by_id(self, user_id: str) -> AuthUser:
        psycopg = self._psycopg()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, full_name FROM users WHERE id = %s",
                    (int(user_id),),
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return AuthUser(id=int(row[0]), email=row[1], full_name=row[2])


class D1AuthBackend:
    def __init__(self) -> None:
        settings.require_d1_auth()
        self.url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{settings.cloudflare_account_id}/d1/database/{settings.d1_database_id}/query"
        )
        self.headers = {
            "Authorization": f"Bearer {settings.d1_api_token}",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def initialize(self) -> None:
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def _query(self, sql: str, params: list[str] | None = None) -> list[dict]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.url, headers=self.headers, json={"sql": sql, "params": params or []})
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"D1 query failed: {response.text}")
        data = response.json()
        result = data.get("result", [])
        if not isinstance(result, list) or not result:
            return []
        first = result[0]
        rows = first.get("results", [])
        return rows if isinstance(rows, list) else []

    def _execute(self, sql: str, params: list[str] | None = None) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.url, headers=self.headers, json={"sql": sql, "params": params or []})
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"D1 query failed: {response.text}")
        data = response.json()
        result = data.get("result", [])
        return result[0] if isinstance(result, list) and result else {}

    def register(self, email: str, password_hash: str, full_name: str | None = None) -> AuthUser:
        existing = self._query("SELECT id FROM users WHERE email = ?", [email])
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        result = self._execute(
            "INSERT INTO users (email, full_name, password_hash) VALUES (?, ?, ?)",
            [email, full_name or "", password_hash],
        )
        user_id = int(result.get("meta", {}).get("last_row_id") or result.get("meta", {}).get("last_rowid") or 0)
        if not user_id:
            rows = self._query("SELECT id FROM users WHERE email = ?", [email])
            if not rows:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to create user in D1")
            user_id = int(rows[0]["id"])
        return AuthUser(id=user_id, email=email, full_name=full_name)

    def authenticate(self, email: str, password: str) -> str:
        rows = self._query("SELECT id, email, password_hash FROM users WHERE email = ?", [email])
        if not rows or not verify_password(password, rows[0]["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return create_access_token(subject=str(rows[0]["id"]), extra_claims={"email": rows[0]["email"]})

    def get_user_by_id(self, user_id: str) -> AuthUser:
        rows = self._query("SELECT id, email, full_name FROM users WHERE id = ?", [user_id])
        if not rows:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        row = rows[0]
        full_name = row.get("full_name") or None
        return AuthUser(id=int(row["id"]), email=row["email"], full_name=full_name)


class AuthService:
    def __init__(self) -> None:
        backend_name = settings.selected_auth_backend()
        if backend_name == "postgres":
            self.backend: AuthBackend = PostgresAuthBackend()
        elif backend_name == "d1":
            self.backend = D1AuthBackend()
        else:
            self.backend = SQLiteAuthBackend()

    def initialize(self) -> None:
        settings.require_auth()
        self.backend.initialize()

    def register(self, email: str, password: str, full_name: str | None = None) -> AuthUser:
        normalized_email = email.strip().lower()
        return self.backend.register(normalized_email, hash_password(password), full_name)

    def authenticate(self, email: str, password: str) -> str:
        normalized_email = email.strip().lower()
        return self.backend.authenticate(normalized_email, password)

    def get_user_by_id(self, user_id: str) -> AuthUser:
        return self.backend.get_user_by_id(user_id)


auth_service = AuthService()
