from __future__ import annotations

from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.models.schemas import ImageAspectRatio, ImageGenerationRequest, ImageGenerationResponse
from app.services.r2 import R2StorageError, r2_storage_service
from app.services.workers_ai import WorkersAIError, workers_ai_service
from app.utils.security import get_current_subject


router = APIRouter(tags=["image"])


MODE_ASPECT_RATIOS: dict[str, ImageAspectRatio] = {
    "simple": "1:1",
    "portrait": "3:4",
    "widescreen_landscape": "16:9",
    "product_photo": "1:1",
}


def _extension_for_content_type(content_type: str) -> str:
    if content_type == "image/jpeg":
        return "jpg"
    if content_type == "image/webp":
        return "webp"
    return "png"


def _augment_prompt(prompt: str, mode: str, aspect_ratio: str, person_generation: str) -> str:
    additions: list[str] = []
    if mode == "portrait":
        additions.append("portrait orientation, vertical composition")
    elif mode == "widescreen_landscape":
        additions.append("widescreen landscape composition, cinematic framing")
    elif mode == "product_photo":
        additions.append("professional product photo, centered composition, clean studio lighting")
    else:
        additions.append("balanced composition")

    if aspect_ratio == "1:1":
        additions.append("square framing")
    elif aspect_ratio == "3:4":
        additions.append("3:4 aspect framing")
    elif aspect_ratio == "4:3":
        additions.append("4:3 aspect framing")
    elif aspect_ratio == "9:16":
        additions.append("9:16 vertical framing")
    elif aspect_ratio == "16:9":
        additions.append("16:9 widescreen framing")

    if person_generation == "dont_allow":
        additions.append("no people")
    elif person_generation == "allow_adult":
        additions.append("adult people allowed, no children")
    else:
        additions.append("people allowed")

    return f"{prompt.strip()}. " + ", ".join(additions)


@router.post(
    "/generate-image",
    response_model=ImageGenerationResponse,
    summary="Generate an image with Workers AI and store it in R2",
    description=(
        "Generate an image with the configured Cloudflare Workers AI model, "
        "apply mode-based prompt shaping and aspect ratio defaults, upload the result to R2, "
        "and return the public object URL."
    ),
)
async def generate_image(
    payload: ImageGenerationRequest,
    _: str = Depends(get_current_subject),
) -> ImageGenerationResponse:
    try:
        aspect_ratio = payload.aspect_ratio or MODE_ASPECT_RATIOS[payload.mode]
        image_bytes, content_type, source_url = await workers_ai_service.generate_image(
            _augment_prompt(payload.prompt, payload.mode, aspect_ratio, payload.person_generation),
            aspect_ratio=aspect_ratio,
            person_generation=payload.person_generation,
            steps=payload.steps,
            seed=payload.seed,
        )
        key = str(PurePosixPath("images") / f"{uuid4().hex}.{_extension_for_content_type(content_type)}")
        url = r2_storage_service.upload_bytes(image_bytes, key, content_type)
        return ImageGenerationResponse(
            key=key,
            url=url,
            source_url=source_url,
            mode=payload.mode,
            aspect_ratio=aspect_ratio,
            person_generation=payload.person_generation,
            model=settings.workers_image_model,
        )
    except (WorkersAIError, R2StorageError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
