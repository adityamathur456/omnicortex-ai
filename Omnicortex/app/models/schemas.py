from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None


class ResumeInput(BaseModel):
    name: str
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    target_role: str
    job_description: str


class ResumeGenerationResponse(BaseModel):
    latex: str
    context_sources: list[str]
    tex_key: str | None = None
    pdf_key: str | None = None
    pdf_url: str | None = None
    latex_url: str | None = None


class CompileResumeRequest(BaseModel):
    latex: str
    filename: str | None = None


class CompileResumeResponse(BaseModel):
    tex_key: str
    pdf_key: str
    pdf_url: str
    latex_url: str | None = None


ImageMode = Literal["simple", "portrait", "widescreen_landscape", "product_photo"]
ImageAspectRatio = Literal["1:1", "3:4", "4:3", "9:16", "16:9"]
PersonGeneration = Literal["dont_allow", "allow_adult", "allow_all"]


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    mode: ImageMode = "simple"
    aspect_ratio: ImageAspectRatio | None = None
    person_generation: PersonGeneration = "dont_allow"
    steps: int = Field(default=4, ge=1, le=8)
    seed: int | None = None


class ImageGenerationResponse(BaseModel):
    key: str
    url: str
    source_url: str | None = None
    mode: ImageMode
    aspect_ratio: ImageAspectRatio
    person_generation: PersonGeneration
    model: str


class MedicalAnalysisResponse(BaseModel):
    modality: str
    findings: str
    possible_conditions: list[str]
    confidence: str
    recommendation: str
    disclaimer: str = "This is AI-assisted analysis, not a medical diagnosis."
    image_url: str


class HealthResponse(BaseModel):
    status: str
    rag_chunks: int
    details: dict[str, Any] = Field(default_factory=dict)
    