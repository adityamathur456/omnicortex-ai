from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel


class CompileRequest(BaseModel):
    latex: str
    filename: str | None = None


class CompileResponse(BaseModel):
    filename: str
    tex_b64: str
    pdf_b64: str


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip('"').strip("'").strip()


LATEX_ENGINE = _env("LATEX_ENGINE", "xelatex") or "xelatex"
LATEX_TIMEOUT_SECONDS = int(_env("LATEX_TIMEOUT_SECONDS", "180") or "180")
COMPILER_AUTH_TOKEN = _env("LATEX_COMPILER_SERVICE_TOKEN")

app = FastAPI(title="OmniCortex LaTeX Compiler", version="1.0.0")


def _resolve_latex_engine(engine: str) -> str:
    resolved = shutil.which(engine)
    if not resolved:
        raise HTTPException(status_code=500, detail=f"{engine} is not installed or not available on PATH")
    return resolved


def _safe_name(filename: str | None) -> str:
    safe_name = "".join(ch for ch in (filename or f"resume-{uuid4().hex}") if ch.isalnum() or ch in "-_")
    return safe_name or f"resume-{uuid4().hex}"


def _require_auth(authorization: str | None) -> None:
    if not COMPILER_AUTH_TOKEN:
        return
    expected = f"Bearer {COMPILER_AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "latex_engine": LATEX_ENGINE}


@app.post("/compile", response_model=CompileResponse)
async def compile_resume(payload: CompileRequest, authorization: str | None = Header(default=None)) -> CompileResponse:
    _require_auth(authorization)
    engine = _resolve_latex_engine(LATEX_ENGINE)
    safe_name = _safe_name(payload.filename)

    with tempfile.TemporaryDirectory(prefix="omnicortex-compiler-") as temp_dir:
        work_dir = Path(temp_dir)
        tex_path = work_dir / f"{safe_name}.tex"
        pdf_path = work_dir / f"{safe_name}.pdf"
        tex_path.write_text(payload.latex, encoding="utf-8")

        command = [engine, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
        for _ in range(2):
            try:
                result = subprocess.run(
                    command,
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=LATEX_TIMEOUT_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                output = ""
                if exc.stdout:
                    output += exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
                if exc.stderr:
                    output += exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{LATEX_ENGINE} timed out after {LATEX_TIMEOUT_SECONDS} seconds. {output[-3000:]}",
                ) from exc
            if result.returncode != 0:
                log = (result.stdout or "") + "\n" + (result.stderr or "")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=log[-4000:])

        if not pdf_path.exists():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Compilation did not produce a PDF")

        return CompileResponse(
            filename=safe_name,
            tex_b64=base64.b64encode(tex_path.read_bytes()).decode("ascii"),
            pdf_b64=base64.b64encode(pdf_path.read_bytes()).decode("ascii"),
        )
