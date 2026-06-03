from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.models.schemas import HealthResponse
from app.routes import auth, image, latex, medical, resume
from app.services.auth_service import auth_service
from app.services.rag import rag_service

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnicortex")


OPENAPI_DESCRIPTION = """
Production-ready FastAPI backend for OmniCortex AI.

### Developers
- Aaditya Mathur
- Arman Hussain

### Core Modules
- JWT authentication with pluggable auth backends (`Postgres`, `D1`, fallback `SQLite`)
- Resume AutoRAG over preloaded PDF resumes
- Resume generation as XeLaTeX with PDF compilation and R2 artifact upload
- Image generation with Cloudflare Workers AI and R2 storage
- Medical image analysis with Cloudflare vision models and structured output

### Cloudflare Architecture
- **Workers AI Text** generates resume LaTeX and other LLM responses.
- **Workers AI Embeddings** power the in-memory/file-backed resume retrieval index.
- **Workers AI Vision** analyzes uploaded medical images and report screenshots.
- **Workers AI Image Models** generate images for `/generate-image`.
- **Cloudflare R2** stores generated PDFs, LaTeX sources, uploaded medical images, and generated images.
- **Cloudflare D1** is optionally supported as an auth database backend.

### Runtime Shape
- Main API runs on `http://localhost:8000`
- LaTeX compiler service runs separately on `http://localhost:8080`
- Docker Compose runs the backend, compiler, and Postgres together
""".strip()

OPENAPI_TAGS = [
    {"name": "auth", "description": "Register users and obtain JWT bearer tokens."},
    {
        "name": "resume",
        "description": "Resume RAG retrieval, XeLaTeX generation, PDF compilation, and R2 artifact publishing.",
    },
    {"name": "latex", "description": "Direct LaTeX-to-PDF compilation and artifact upload workflows."},
    {"name": "image", "description": "Cloudflare Workers AI image generation with R2-backed public URLs."},
    {
        "name": "medical",
        "description": "Medical image upload, Cloudflare vision analysis, response normalization, and disclaimer handling.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_runtime_dirs()
    auth_service.initialize()
    try:
        await rag_service.initialize()
        logger.info("RAG initialized with %s chunks", len(rag_service.chunks))
    except Exception as exc:
        logger.warning("RAG initialization skipped or failed: %s", exc)
    yield


app = FastAPI(
    title="OmniCortex AI Backend",
    version="1.0.0",
    description=OPENAPI_DESCRIPTION,
    lifespan=lifespan,
    contact={"name": "Aaditya Mathur and Arman Hussain"},
    openapi_tags=OPENAPI_TAGS,
    servers=[
        {"url": "http://localhost:8000", "description": "Localhost / Docker-exposed backend"},
        {"url": "http://127.0.0.1:8000", "description": "Localhost loopback backend"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(latex.router)
app.include_router(image.router)
app.include_router(medical.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    schema.setdefault("info", {})["contact"] = {"name": "Aaditya Mathur and Arman Hussain"}
    schema["info"]["x-developers"] = [
        {"name": "Aaditya Mathur"},
        {"name": "Arman Hussain"},
    ]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Backend health check",
    description="Return service health, RAG chunk count, selected auth backend, compiler target, and active model configuration.",
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        rag_chunks=len(rag_service.chunks),
        details={
            "auth_backend": settings.selected_auth_backend(),
            "latex_compiler_service_url": settings.latex_compiler_service_url or "local-fallback",
            "text_model": settings.workers_text_model,
            "image_model": settings.workers_image_model,
            "medical_model": settings.workers_medical_model,
            "medical_vision_model": settings.workers_medical_vision_model,
            "embedding_model": settings.workers_embedding_model,
        },
    )
