from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import settings
from app.services.workers_ai import workers_ai_service
from app.utils.chunking import chunk_text
from app.utils.pdf_parser import extract_pdf_text


@dataclass
class VectorChunk:
    id: str
    source: str
    text: str
    embedding: list[float]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class RAGService:
    def __init__(self) -> None:
        self.chunks: list[VectorChunk] = []

    def _load_file_index(self) -> bool:
        path = settings.vector_store_path
        if not path.exists():
            return False
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.chunks = [VectorChunk(**item) for item in data.get("chunks", [])]
        return bool(self.chunks)

    def _save_file_index(self) -> None:
        settings.ensure_runtime_dirs()
        payload = {"chunks": [asdict(chunk) for chunk in self.chunks]}
        with settings.vector_store_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def _find_resume_pdfs(self) -> list[Path]:
        paths: list[Path] = []
        for directory in settings.existing_resume_dirs():
            paths.extend(sorted(directory.glob("*.pdf")))
        seen: set[Path] = set()
        unique_paths: list[Path] = []
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_paths.append(path)
        return unique_paths[:10]

    async def initialize(self, force_rebuild: bool = False) -> None:
        settings.ensure_runtime_dirs()
        if not force_rebuild and self._load_file_index():
            return

        pdf_paths = self._find_resume_pdfs()
        chunks: list[VectorChunk] = []
        for pdf_path in pdf_paths:
            text = extract_pdf_text(pdf_path)
            for index, chunk in enumerate(chunk_text(text, settings.chunk_size, settings.chunk_overlap)):
                embedding = await workers_ai_service.get_embedding(chunk)
                chunks.append(
                    VectorChunk(
                        id=f"{pdf_path.stem}-{index}",
                        source=str(pdf_path),
                        text=chunk,
                        embedding=embedding,
                    )
                )
        self.chunks = chunks
        self._save_file_index()

    async def retrieve(self, query: str, top_k: int | None = None) -> list[VectorChunk]:
        if not self.chunks:
            await self.initialize()
        if not self.chunks:
            return []
        query_embedding = await workers_ai_service.get_embedding(query)
        ranked = sorted(
            self.chunks,
            key=lambda chunk: _cosine_similarity(query_embedding, chunk.embedding),
            reverse=True,
        )
        return ranked[: top_k or settings.rag_top_k]

rag_service = RAGService()