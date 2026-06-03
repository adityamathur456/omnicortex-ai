from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from app.config import settings


class WorkersAIError(RuntimeError):
    pass


class WorkersAIService:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(90.0, connect=20.0)
        self._vision_license_agreed = False

    def _url(self, model: str) -> str:
        settings.require_workers_ai()
        return (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{settings.cloudflare_account_id}/ai/run/{model}"
        )

    def _gateway_url(self, model: str) -> str:
        settings.require_imagen_ai()
        return (
            "https://gateway.ai.cloudflare.com/v1/"
            f"{settings.cloudflare_account_id}/{settings.cloudflare_ai_gateway_id}/workers-ai/{model}"
        )

    def _headers(self, content_type: str = "application/json", token: str | None = None) -> dict[str, str]:
        if token is None:
            settings.require_workers_ai()
        return {
            "Authorization": f"Bearer {token or settings.cloudflare_workers_auth_token}",
            "Content-Type": content_type,
        }

    @staticmethod
    def _error_message(prefix: str, response: httpx.Response) -> str:
        body = response.text[:2000]
        if response.status_code == 401 and "Authentication error" in body:
            return (
                f"{prefix}: 401 Authentication error from Cloudflare. "
                "The configured CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_WORKERS_AUTH_TOKEN are not authorized "
                "for Workers AI. Create a dedicated Workers AI API token, or grant the token Workers AI Read/Edit "
                "on that account, then restart the backend so it reloads the environment."
            )
        return f"{prefix}: {response.status_code} {body}"

    async def _post_json(self, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self._url(model), headers=self._headers(), json=payload)
        if response.status_code >= 400:
            raise WorkersAIError(self._error_message("Workers AI request failed", response))
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise WorkersAIError("Workers AI returned a non-JSON response") from exc
        if data.get("success") is False:
            raise WorkersAIError(f"Workers AI error: {data.get('errors') or data}")
        return data

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        result = data.get("result", data)
        if isinstance(result, str):
            return result
        for key in ("response", "text", "output", "generated_text"):
            value = result.get(key) if isinstance(result, dict) else None
            if isinstance(value, str):
                return value
        if isinstance(result, dict) and isinstance(result.get("choices"), list) and result["choices"]:
            message = result["choices"][0].get("message", {})
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        raise WorkersAIError(f"Unable to extract text from Workers AI response: {data}")

    @staticmethod
    def _extract_embedding(data: dict[str, Any]) -> list[float]:
        result = data.get("result", data)
        candidate: Any = None
        if isinstance(result, dict):
            candidate = result.get("data") or result.get("embeddings") or result.get("embedding")
        elif isinstance(result, list):
            candidate = result

        if isinstance(candidate, list) and candidate:
            first = candidate[0]
            if isinstance(first, dict) and isinstance(first.get("embedding"), list):
                return [float(value) for value in first["embedding"]]
            if isinstance(first, list):
                return [float(value) for value in first]
            if isinstance(first, (int, float)):
                return [float(value) for value in candidate]
        raise WorkersAIError(f"Unable to extract embedding from Workers AI response: {data}")

    async def generate_text(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._post_json(model or settings.workers_text_model, payload)
        return self._extract_text(data)

    async def get_embedding(self, text: str) -> list[float]:
        data = await self._post_json(settings.workers_embedding_model, {"text": [text]})
        return self._extract_embedding(data)

    async def generate_image(
        self,
        prompt: str,
        *,
        aspect_ratio: str,
        person_generation: str,
        steps: int = 4,
        seed: int | None = None,
    ) -> tuple[bytes, str, str | None]:
        model = settings.workers_image_model

        if model == "google/imagen-4":
            settings.require_imagen_ai()
            payload = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }
            if not settings.cloudflare_imagen_proxy_url:
                raise WorkersAIError(
                    "google/imagen-4 requires CLOUDFLARE_IMAGEN_PROXY_URL. "
                    "Set WORKERS_IMAGE_MODEL=@cf/black-forest-labs/flux-1-schnell to use Workers AI directly."
                )
            headers = {"Content-Type": "application/json"}
            if settings.imagen_proxy_auth_token:
                headers["Authorization"] = f"Bearer {settings.imagen_proxy_auth_token}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(settings.cloudflare_imagen_proxy_url, headers=headers, json=payload)
            if response.status_code >= 400:
                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type:
                    raise WorkersAIError(
                        f"Imagen proxy request failed: {response.status_code}. "
                        "The Cloudflare Worker threw an exception. Redeploy the patched Worker and check returned JSON."
                    )
                raise WorkersAIError(f"Imagen proxy request failed: {response.status_code} {response.text[:2000]}")
            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                raise WorkersAIError("Imagen proxy returned a non-JSON response") from exc
            image_value = data.get("image")
            if not isinstance(image_value, str):
                raise WorkersAIError(f"Imagen proxy response did not include an image URL: {data}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                image_response = await client.get(image_value)
            if image_response.status_code >= 400:
                raise WorkersAIError(
                    f"Generated image URL download failed: {image_response.status_code} {image_response.text}"
                )
            downloaded_content_type = image_response.headers.get("content-type", "image/png").split(";", 1)[0]
            return image_response.content, downloaded_content_type, image_value

        settings.require_workers_ai()
        payload: dict[str, Any] = {
            "prompt": prompt,
            "steps": steps,
        }
        if seed is not None:
            payload["seed"] = seed

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._url(model),
                headers=self._headers(),
                json=payload,
            )
        if response.status_code >= 400:
            raise WorkersAIError(self._error_message("Workers AI image request failed", response))

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("image/"):
            return response.content, content_type.split(";", 1)[0], None

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise WorkersAIError("Workers AI image endpoint returned an unsupported response") from exc
        result = data.get("result", data)
        image_value = None
        if isinstance(result, dict):
            image_value = result.get("image") or result.get("base64") or result.get("b64_json")
        if not isinstance(image_value, str):
            raise WorkersAIError(f"Unable to extract image bytes from Workers AI response: {data}")
        if image_value.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                image_response = await client.get(image_value)
            if image_response.status_code >= 400:
                raise WorkersAIError(
                    f"Generated image URL download failed: {image_response.status_code} {image_response.text}"
                )
            downloaded_content_type = image_response.headers.get("content-type", "image/png").split(";", 1)[0]
            return image_response.content, downloaded_content_type, image_value
        if image_value.startswith("data:"):
            image_value = image_value.split(",", 1)[1]
        return base64.b64decode(image_value), "image/png", None

    async def _ensure_medical_vision_license(self) -> None:
        if self._vision_license_agreed:
            return
        try:
            await self._post_json(settings.workers_medical_vision_model, {"prompt": "agree", "max_tokens": 8})
        except WorkersAIError as exc:
            message = str(exc)
            if "Thank you for agreeing to this model's terms" not in message:
                raise
        self._vision_license_agreed = True

    async def analyze_medical_image(
        self,
        image_bytes: bytes,
        content_type: str,
        modality_hint: str | None = None,
    ) -> str:
        await self._ensure_medical_vision_license()
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        modality_line = ""
        if modality_hint:
            modality_line = (
                f"Modality hint from the caller: {modality_hint}. "
                "Use this as the primary modality unless the image clearly contradicts it. "
            )
        prompt = (
            "You are an AI assistant helping summarize medical images for educational triage. "
            "Do not claim to diagnose. "
            f"{modality_line}"
            "Analyze this medical input, which may be an MRI, CT, ultrasound, X-ray, PET, angiography, 2D echo, "
            "blood report image, or serum report image, and return only valid JSON "
            'with keys: modality, findings, possible_conditions, confidence, recommendation. '
            "If modality is uncertain, return modality as Unknown instead of guessing. "
            "If the input is a report image rather than a radiology scan, identify the report type as modality "
            "such as Blood Report or Serum and summarize the visible abnormalities or flagged values. "
            'The recommendation must be exactly "Consult a doctor".'
        )
        payload = {
            "prompt": prompt,
            "image": f"data:{content_type};base64,{image_b64}",
            "temperature": 0.1,
            "max_tokens": 500,
        }
        data = await self._post_json(settings.workers_medical_vision_model, payload)
        return self._extract_text(data)


workers_ai_service = WorkersAIService()
