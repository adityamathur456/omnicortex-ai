from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx

from app.config import settings


class LatexCompilationError(RuntimeError):
    pass


def _resolve_latex_engine(engine: str) -> str:
    resolved = shutil.which(engine)
    if resolved:
        return resolved

    candidates = [
        Path.home() / "AppData" / "Local" / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64" / f"{engine}.exe",
        Path("C:/Program Files/MiKTeX/miktex/bin/x64") / f"{engine}.exe",
        Path("C:/Program Files (x86)/MiKTeX/miktex/bin") / f"{engine}.exe",
    ]
    for candidate in candidates:
        try:
            exists = candidate.exists()
        except PermissionError:
            exists = True
        if exists:
            return str(candidate)

    raise LatexCompilationError(f"{engine} is not installed or not available on PATH")


class LatexCompilerService:
    def compile_to_bytes(self, latex: str, filename: str | None = None) -> tuple[str, bytes, bytes]:
        engine = settings.latex_engine
        engine_path = _resolve_latex_engine(engine)

        safe_name = "".join(ch for ch in (filename or f"resume-{uuid4().hex}") if ch.isalnum() or ch in "-_")
        if not safe_name:
            safe_name = f"resume-{uuid4().hex}"

        with tempfile.TemporaryDirectory(prefix="omnicortex-latex-") as temp_dir:
            work_dir = Path(temp_dir)
            tex_path = work_dir / f"{safe_name}.tex"
            pdf_path = work_dir / f"{safe_name}.pdf"
            tex_path.write_text(latex, encoding="utf-8")

            command = [engine_path, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
            for _ in range(2):
                try:
                    result = subprocess.run(
                        command,
                        cwd=work_dir,
                        capture_output=True,
                        text=True,
                        timeout=settings.latex_timeout_seconds,
                        check=False,
                    )
                except subprocess.TimeoutExpired as exc:
                    output = ""
                    if exc.stdout:
                        output += exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
                    if exc.stderr:
                        output += exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
                    details = output[-3000:] if output else "No compiler output captured before timeout."
                    raise LatexCompilationError(
                        f"{engine} timed out after {settings.latex_timeout_seconds} seconds. {details}"
                    ) from exc
                if result.returncode != 0:
                    log = (result.stdout or "") + "\n" + (result.stderr or "")
                    raise LatexCompilationError(log[-4000:])

            if not pdf_path.exists():
                raise LatexCompilationError(f"{engine} completed without producing a PDF")

            return safe_name, tex_path.read_bytes(), pdf_path.read_bytes()


class LatexCompilerClient:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(float(settings.latex_compiler_service_timeout_seconds), connect=20.0)

    def compile_to_bytes(self, latex: str, filename: str | None = None) -> tuple[str, bytes, bytes]:
        if not settings.latex_compiler_service_url:
            return LatexCompilerService().compile_to_bytes(latex, filename)

        headers = {"Content-Type": "application/json"}
        if settings.latex_compiler_service_token:
            headers["Authorization"] = f"Bearer {settings.latex_compiler_service_token}"

        payload = {"latex": latex, "filename": filename}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(settings.latex_compiler_service_url.rstrip("/") + "/compile", headers=headers, json=payload)
        if response.status_code >= 400:
            raise LatexCompilationError(f"Compiler service failed: {response.status_code} {response.text[:4000]}")
        data = response.json()
        try:
            safe_name = str(data["filename"])
            tex_bytes = base64.b64decode(data["tex_b64"])
            pdf_bytes = base64.b64decode(data["pdf_b64"])
        except (KeyError, ValueError) as exc:
            raise LatexCompilationError(f"Compiler service returned an invalid payload: {data}") from exc
        return safe_name, tex_bytes, pdf_bytes


latex_compiler_client = LatexCompilerClient()
