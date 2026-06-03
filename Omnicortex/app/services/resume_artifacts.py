from __future__ import annotations

from pathlib import PurePosixPath

from app.models.schemas import CompileResumeResponse
from app.services.latex_compiler import latex_compiler_client
from app.services.r2 import r2_storage_service


def compile_and_upload_resume(latex: str, filename: str | None = None) -> CompileResumeResponse:
    base_name, tex_bytes, pdf_bytes = latex_compiler_client.compile_to_bytes(latex, filename)
    pdf_key = str(PurePosixPath("resumes/generated") / f"{base_name}.pdf")
    tex_key = str(PurePosixPath("resumes/generated") / f"{base_name}.tex")
    pdf_url = r2_storage_service.upload_bytes(pdf_bytes, pdf_key, "application/pdf")
    latex_url = r2_storage_service.upload_bytes(tex_bytes, tex_key, "application/x-tex")
    return CompileResumeResponse(tex_key=tex_key, pdf_key=pdf_key, pdf_url=pdf_url, latex_url=latex_url)
