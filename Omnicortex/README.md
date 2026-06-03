# OmniCortex AI Backend

Production-oriented FastAPI backend for Cloudflare Workers AI, Cloudflare R2, RAG over resume PDFs, LaTeX resume compilation, image generation, medical image analysis, JWT auth, and CORS.

## Setup

1. Create `.env` from `.env.example` and fill in secrets. Use a 32+ byte `JWT_SECRET_KEY`. Do not commit `.env`.
   For `CLOUDFLARE_WORKERS_AUTH_TOKEN`, use a dedicated Workers AI API token or an API token with
   `Workers AI Read` and `Workers AI Edit` on the target account.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure auth with either PostgreSQL or Cloudflare D1.
4. Configure a separate LaTeX compiler service for production using `compiler_service/`.
5. Put up to 10 resume PDFs in `data/resumes/`. This project also falls back to the existing `resumes/` folder.
6. Run:

```bash
uvicorn app.main:app --reload
```

## Auth Flow

- `POST /auth/register`
- `POST /auth/login`
- Use the returned bearer token on protected routes.

### Auth Backends

Set `AUTH_BACKEND=postgres` and provide `POSTGRES_DSN`, or set `AUTH_BACKEND=d1` and provide `CLOUDFLARE_ACCOUNT_ID`, `D1_DATABASE_ID`, and `D1_API_TOKEN`.

SQLite remains as a local fallback when neither Postgres nor D1 is configured, but the deployment-safe path is Postgres or D1.

## Protected AI Routes

- `POST /generate-resume`
- `POST /compile-resume`
- `POST /generate-image`
- `POST /analyze-medical`

### Generate Resume Input

`POST /generate-resume` accepts raw `text/plain`, not structured JSON.

Example body:

```text
name Aditya Mathur, profession software engineer, skills Python, FastAPI, React, AWS, Cloudflare, Docker, SQL, experience built production APIs with JWT and R2 storage, projects OmniCortex AI backend with Workers AI and RAG, target role backend software engineer, job description hiring for Python FastAPI cloud AI backend engineer
```

## Notes

- RAG embeddings are generated at startup and persisted to `storage/vector_store.json`.
- Generated PDFs and TeX files are uploaded to R2 under `resumes/generated/`.
- Generated images are uploaded to R2 under `images/`.
- Medical uploads are stored under `medical/` and the response always includes: `This is AI-assisted analysis, not a medical diagnosis.`
- Resume compilation can be offloaded to a separate container service using `LATEX_COMPILER_SERVICE_URL`. The main backend then uploads returned PDF/TeX bytes to R2 and does not rely on persistent local temp files.

## LaTeX Compiler Service

The compiler microservice lives in `compiler_service/`.

Build and run it separately:

```bash
cd compiler_service
docker build -t omnicortex-latex-compiler .
docker run -p 8080:8080 omnicortex-latex-compiler
```

Then point the main backend at it:

```env
LATEX_COMPILER_SERVICE_URL=http://your-compiler-service:8080
LATEX_COMPILER_SERVICE_TOKEN=
```
- Medical analysis uses `@cf/meta/llama-3.2-11b-vision-instruct` with a base64 `data:` image payload, because the text-only Llama 3.3 model does not accept image content in Workers AI.

The default image model is `@cf/black-forest-labs/flux-1-schnell`, called through the normal Workers AI API. Imagen 4 proxy support remains in `cloudflare/imagen-worker` for later use after AI Gateway balance or BYOK is configured.

`POST /generate-image` body:

```json
{
  "prompt": "A premium product photo of a blue ceramic mug on a white background",
  "mode": "product_photo",
  "person_generation": "dont_allow"
}
```

Supported `mode` values:

- `simple` -> `1:1`
- `portrait` -> `3:4`
- `widescreen_landscape` -> `16:9`
- `product_photo` -> `1:1`

You can override `aspect_ratio` with `1:1`, `3:4`, `4:3`, `9:16`, or `16:9`.

Supported `person_generation` values: `dont_allow`, `allow_adult`, `allow_all`.
