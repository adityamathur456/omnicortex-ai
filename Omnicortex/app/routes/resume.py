from __future__ import annotations

import re

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.config import settings
from app.models.schemas import ResumeGenerationResponse
from app.services.latex_compiler import LatexCompilationError
from app.services.rag import rag_service
from app.services.r2 import R2StorageError
from app.services.resume_artifacts import compile_and_upload_resume
from app.services.tools import AgentTool, agentic_pipeline
from app.services.workers_ai import WorkersAIError, workers_ai_service
from app.utils.security import get_current_subject


router = APIRouter(tags=["resume"])


RESUME_TEMPLATE = r"""
\documentclass[10pt, a4paper]{article}

% ---------- packages ----------
\usepackage{fontspec}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{tabularx}
\usepackage{array}

% ---------- page geometry ----------
\geometry{
  top    = 0.50in,
  bottom = 0.35in,
  left   = 0.62in,
  right  = 0.62in
}

% ---------- fonts ----------
\setmainfont{Latin Modern Roman}

% ---------- colors ----------
\definecolor{sectioncolor}{RGB}{0,0,0}
\definecolor{linkcolor}{RGB}{0,0,0}

% ---------- hyperlinks ----------
\hypersetup{
  colorlinks = true,
  urlcolor   = linkcolor,
  hidelinks
}

% ---------- section heading style ----------
\titleformat{\section}
  {\large\bfseries\uppercase}
  {}
  {0em}
  {}
  [\titlerule]
\titlespacing{\section}{0pt}{6pt}{4pt}

% ---------- bullet style ----------
\setlist[itemize]{
  leftmargin = 1.2em,
  itemsep    = 1pt,
  topsep     = 2pt,
  parsep     = 0pt,
  label      = \textbullet
}

% ---------- helper commands ----------
\newcommand{\jobheading}[4]{%
  \noindent
  \textbf{#1}, \textit{#2} \hfill #3, #4 \\[-4pt]
}

\newcommand{\projectheading}[3]{%
  \noindent
  \textbf{#1}%
  \ifx&#2&\else{} $|$ \textit{#2}\fi%
  \ifx&#3&\else{} $|$ \href{#3}{\underline{Link}}\fi \\[-4pt]
}

\newcommand{\eduheading}[4]{%
  \noindent
  \textbf{#1} \hfill #3 \\
  \textit{#2} \hfill \textit{#4} \\[-4pt]
}

\begin{document}
\pagestyle{empty}

\begin{center}
  {\LARGE\bfseries <<FULL NAME>>}\\[4pt]
  \small
  <<email@example.com>>
  \enspace|\enspace
  \href{<<PORTFOLIO OR LINKEDIN URL>>}{<<DISPLAY TEXT e.g. linkedin.com/in/yourname>>}
\end{center}

\vspace{2pt}

\section{About Me}

<<Two to three concise lines summarizing professional identity, target role, strongest technical domains, and measurable value. Keep it specific and recruiter-ready.>>

\vspace{2pt}

\section{Work Experience}

\jobheading{<<Company Name>>}{<<Job Title>>}{<<Month YYYY -- Month YYYY>>}{<<City, State/Country>>}
\begin{itemize}
  \item <<Action verb + task/responsibility + quantified result.>>
  \item <<Action verb + task/responsibility + quantified result.>>
\end{itemize}

\vspace{2pt}

\jobheading{<<Company Name>>}{<<Job Title>>}{<<Month YYYY -- Month YYYY>>}{<<City, State/Country>>}
\begin{itemize}
  \item <<Action verb + task/responsibility + quantified result.>>
  \item <<Action verb + task/responsibility + quantified result.>>
\end{itemize}

\section{Projects}

\projectheading{<<Project Title>>}{<<Tech Stack e.g. React, Node.js, MongoDB>>}{<<Live URL or GitHub URL or leave empty>>}
\begin{itemize}
  \item <<One-sentence description of what the project does and the problem it solves.>>
  \item <<Implementation detail: tech choices, architecture, or notable feature.>>
\end{itemize}

\vspace{2pt}

\projectheading{<<Project Title>>}{<<Tech Stack>>}{}
\begin{itemize}
  \item <<One-sentence description.>>
  \item <<Implementation detail or quantified outcome.>>
\end{itemize}

\section{Education}

\eduheading
  {<<University / Institution Name>>}
  {<<Degree, e.g. B.Tech in Computer Engineering (CGPA: 9.27)>>}
  {<<Month YYYY -- Month YYYY>>}
  {<<City, State/Country>>}
\begin{itemize}
  \item <<Relevant coursework: Course 1, Course 2, Course 3 ...>>
\end{itemize}

\section{Skills}

\begin{tabularx}{\linewidth}{@{} l X @{}}
  \textbf{Languages}            & <<e.g. Python, C++, Java, SQL, JavaScript>> \\[2pt]
  \textbf{Frameworks \& Tools}  & <<e.g. PyTorch, TensorFlow, React, Node.js, Git, Docker>> \\[2pt]
  \textbf{Cloud \& Platforms}   & <<e.g. AWS, GCP, Azure>> \\[2pt]
\end{tabularx}

\section{Achievements}

\begin{itemize}
  \item <<e.g. Solved 1000+ problems on LeetCode, maintaining a streak of 700+ days.>>
  \item <<e.g. Highest rating of 1871 on CodeChef; ranked in top 8\% globally on LeetCode.>>
\end{itemize}

\end{document}
""".strip()


def _resume_prompt(raw_prompt: str, context: str) -> str:
    return f"""
You are a professional resume writer. Fill the provided XeLaTeX resume template using the candidate prompt.

STRICT RULES:
1. Output ONLY valid XeLaTeX code. No explanation, no markdown fences.
2. Keep the template preamble, packages, helper commands, geometry, font, colors, and section style exactly as-is.
   The resume must use only Latin Modern Roman / standard LaTeX serif styling. Do not change \setmainfont or add any other font.
3. Replace every <<PLACEHOLDER>> with real content.
4. Do not leave placeholder markers in the final output.
5. Each bullet point must start with an action verb.
6. Quantify achievements wherever possible using percentages, scale, latency, users, revenue, time saved, or other metrics.
7. Dates format: Month YYYY -- Month YYYY. For current roles write: Month YYYY -- Present.
8. Keep the resume to one A4 page and fill the page naturally. Aim to leave only about three blank lines at the bottom; avoid both cramped overflow and a half-empty page.
9. Use the About Me section for a polished 2-3 line professional summary. It must not be generic; tie it to the candidate's role, skills, strongest projects, and target job.
10. Sections order: About Me, Work Experience, Projects, Education, Skills, Achievements. Swap Education and Work Experience for fresh graduates with no experience.
11. The Achievements section is optional. Include only for competitive programming ratings, awards, hackathons, scholarships, publications, or notable measurable wins.
12. You may professionally rewrite, expand, and strengthen the candidate's raw notes. If the page has too much empty space, add stronger project bullets, skill categories, or relevant coursework based on supplied facts.
13. Do not invent company names, degrees, dates, certifications, links, phone numbers, or locations if not supplied. If important data is missing, omit that field or use a neutral concise value.
14. Escape LaTeX special characters in user content.
15. Use the relevant resume knowledge-base context only for style, phrasing, structure, and seniority calibration.

Candidate raw prompt:
{raw_prompt}

Relevant resume knowledge-base context:
{context}

Template to fill:
{RESUME_TEMPLATE}
""".strip()


def _filename_from_prompt(raw_prompt: str) -> str:
    match = re.search(r"\bname\s*[:=-]?\s*([^,\n;|]+)", raw_prompt, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    words = re.findall(r"[A-Za-z0-9]+", raw_prompt)
    if words:
        return "-".join(words[:4])
    return "generated-resume"


def _clean_latex(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```latex").removeprefix("```tex").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


@router.post(
    "/generate-resume",
    response_model=ResumeGenerationResponse,
    summary="Generate resume, compile PDF, and upload to R2",
    description=(
        "Accept a raw text/plain candidate prompt, retrieve resume context from the AutoRAG index, "
        "generate XeLaTeX with Workers AI, compile it through the configured LaTeX compiler service, "
        "and upload both .tex and .pdf artifacts to Cloudflare R2."
    ),
)
async def generate_resume(
    prompt: str = Body(
        ...,
        media_type="text/plain",
        description="Raw resume prompt, for example: name Aditya Mathur, profession software engineer, skills FastAPI...",
    ),
    _: str = Depends(get_current_subject),
) -> ResumeGenerationResponse:
    try:
        raw_prompt = prompt.strip()
        if len(raw_prompt) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume prompt must be at least 10 characters.",
            )

        async def retrieve_context():
            return await rag_service.retrieve(raw_prompt, top_k=settings.rag_top_k)

        outputs = await agentic_pipeline.execute(
            [
                AgentTool(
                    name="retrieve_resume_context",
                    description="Embed the job description and retrieve relevant resume examples.",
                    run=retrieve_context,
                )
            ]
        )
        chunks = outputs["retrieve_resume_context"]
        context = "\n\n".join(chunk.text for chunk in chunks)
        latex = await workers_ai_service.generate_text(
            _resume_prompt(raw_prompt, context),
            model=settings.workers_text_model,
            temperature=0.25,
            max_tokens=4096,
            system_prompt="You are an elite technical resume writer and LaTeX expert.",
        )
        clean_latex = _clean_latex(latex)
        artifact = compile_and_upload_resume(clean_latex, _filename_from_prompt(raw_prompt))
        return ResumeGenerationResponse(
            latex=clean_latex,
            context_sources=[chunk.source for chunk in chunks],
            tex_key=artifact.tex_key,
            pdf_key=artifact.pdf_key,
            pdf_url=artifact.pdf_url,
            latex_url=artifact.latex_url,
        )
    except LatexCompilationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Resume LaTeX was generated but PDF compilation failed: {exc}",
        ) from exc
    except R2StorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except (RuntimeError, WorkersAIError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
