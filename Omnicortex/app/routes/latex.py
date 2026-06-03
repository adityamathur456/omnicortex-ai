from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import CompileResumeRequest, CompileResumeResponse
from app.services.latex_compiler import LatexCompilationError
from app.services.r2 import R2StorageError
from app.services.resume_artifacts import compile_and_upload_resume
from app.utils.security import get_current_subject


router = APIRouter(tags=["latex"])


@router.post(
    "/compile-resume",
    response_model=CompileResumeResponse,
    summary="Compile LaTeX resume and upload artifacts to R2",
    description=(
        "Compile caller-supplied LaTeX through the configured XeLaTeX compiler path, "
        "then upload the generated PDF and source .tex file to Cloudflare R2."
    ),
)
async def compile_resume(
    payload: CompileResumeRequest,
    _: str = Depends(get_current_subject),
) -> CompileResumeResponse:
    try:
        return compile_and_upload_resume(payload.latex, payload.filename)
    except LatexCompilationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except R2StorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
