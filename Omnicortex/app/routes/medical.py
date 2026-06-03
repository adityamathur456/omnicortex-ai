from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.models.schemas import MedicalAnalysisResponse
from app.services.r2 import R2StorageError, r2_storage_service
from app.services.workers_ai import WorkersAIError, workers_ai_service
from app.utils.security import get_current_subject


router = APIRouter(tags=["medical"])


def _clean_medical_text(value: str) -> str:
    cleaned = re.sub(r"[*_`#]+", "", value)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" ,.;:")


def _parse_medical_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return _parse_medical_fallback(text)


def _parse_medical_fallback(text: str) -> dict:
    cleaned = _clean_medical_text(text)

    modality_patterns = [
        (r"\b2D\s*Echo\b|\b2DEcho\b|\bEchocardiography\b", "2D Echo"),
        (r"\bBlood\s*Report\b|\bCBC\b|\bComplete Blood Count\b", "Blood Report"),
        (r"\bSerum\b|\bSerum\s*Report\b", "Serum"),
        (r"\bAngiography\b|\bAngiogram\b", "Angiography"),
        (r"\bUltrasound\b|\bUSG\b|\bSonography\b", "Ultrasound"),
        (r"\bX-ray\b|\bXray\b", "X-ray"),
        (r"\bMRI\b", "MRI"),
        (r"\bCT\b|\bCAT\s*Scan\b", "CT"),
        (r"\bPET\b", "PET"),
    ]
    modality = "Unknown"
    for pattern, label in modality_patterns:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            modality = label
            break

    findings = cleaned
    findings_match = re.search(r"(?:findings suggest|findings:|shows|showing)\s+(.*?)(?:recommendation:|confidence|$)", cleaned, flags=re.IGNORECASE)
    if findings_match:
        findings = findings_match.group(1).strip(" .")

    confidence_match = re.search(r"\b(low|medium|high)\b", cleaned, flags=re.IGNORECASE)
    confidence = confidence_match.group(1).lower() if confidence_match else "unknown"

    recommendation_match = re.search(r"recommendation:\s*(.*)$", cleaned, flags=re.IGNORECASE)
    recommendation = recommendation_match.group(1).strip() if recommendation_match else "Consult a doctor"

    possible_conditions: list[str] = []
    conditions_match = re.search(
        r"(?:possible condition[s]? such as|possible conditions? include|possible conditions?:)\s*(.*?)(?:\.|recommendation:|confidence|$)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if conditions_match:
        raw_conditions = re.split(r",|/|\bor\b|\band\b", conditions_match.group(1))
        possible_conditions = [_clean_medical_text(item) for item in raw_conditions if _clean_medical_text(item)]

    return {
        "modality": modality,
        "findings": _clean_medical_text(findings) or "No findings returned by model.",
        "possible_conditions": possible_conditions,
        "confidence": confidence,
        "recommendation": _clean_medical_text(recommendation) or "Consult a doctor",
    }


@router.post(
    "/analyze-medical",
    response_model=MedicalAnalysisResponse,
    summary="Analyze medical image and return structured findings",
    description=(
        "Upload a medical image, store it in R2, analyze it with the configured Cloudflare vision model, "
        "and normalize the response into a fixed JSON schema with an explicit disclaimer."
    ),
)
async def analyze_medical(
    file: UploadFile = File(...),
    modality_hint: str | None = Form(default=None),
    _: str = Depends(get_current_subject),
) -> MedicalAnalysisResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload an image file")

    try:
        suffix = (file.filename or "medical.png").split(".")[-1].lower()
        key = str(PurePosixPath("medical") / f"{uuid4().hex}.{suffix}")
        image_bytes = await file.read()
        image_url = r2_storage_service.upload_bytes(image_bytes, key, file.content_type)
        analysis_text = await workers_ai_service.analyze_medical_image(
            image_bytes,
            file.content_type,
            modality_hint=modality_hint,
        )
        data = _parse_medical_json(analysis_text)
        return MedicalAnalysisResponse(
            modality=str(data.get("modality") or "Unknown"),
            findings=str(data.get("findings") or "No findings returned by model."),
            possible_conditions=list(data.get("possible_conditions") or []),
            confidence=str(data.get("confidence") or "Unknown"),
            recommendation=str(data.get("recommendation") or "Consult a doctor"),
            image_url=image_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except (WorkersAIError, R2StorageError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
