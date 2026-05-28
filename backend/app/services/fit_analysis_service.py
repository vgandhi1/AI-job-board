"""On-demand job-fit analysis (pros/cons/summary).

Provider-agnostic: routes to OpenAI or Ollama (`/v1/chat/completions`) based
on `LLM_PROVIDER`. The Ollama OpenAI-compatible endpoint honours
`response_format={"type": "json_object"}` for capable models (llama3.1,
qwen2.5, etc.); smaller models may return prose that fails strict JSON
parsing - we fall back to a generic response in that case.
"""
import json
import logging

from app.config import settings
from app.schemas import JobFitAnalysis
from app.services.llm_client import get_analysis_model, get_llm_client

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """You are an expert technical recruiter. Analyze the alignment between the candidate's query and the job description.

Candidate Query: {user_query}

Job Description: {job_description}

Provide a professional analysis in JSON format with the following structure:
{{
    "analysis_summary": "A professional 1-sentence overview of the match",
    "pros": ["Key alignment point 1", "Key alignment point 2"],
    "cons": ["Potential missing requirement 1", "Potential mismatch 1"]
}}

Be specific, professional, and constructive. Focus on technical skills, experience level, and role fit."""


async def analyze_job_fit(user_query: str, job_description: str) -> JobFitAnalysis:
    """Return pros / cons / summary for `user_query` vs `job_description`."""
    client = get_llm_client()
    prompt = _PROMPT_TEMPLATE.format(
        user_query=user_query, job_description=job_description
    )

    try:
        response = await client.chat.completions.create(
            model=get_analysis_model(),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical recruiter. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
    except Exception as e:
        # Do not echo the raw exception (may contain prompt content / PII)
        # to callers. Log only the class name; the trace stays server-side.
        logger.warning(
            "Fit analysis call failed (provider=%s): %s",
            settings.llm_provider, type(e).__name__,
        )
        raise ValueError("Fit analysis is currently unavailable") from e

    content = response.choices[0].message.content or "{}"
    try:
        analysis_data = json.loads(content)
    except json.JSONDecodeError:
        logger.info(
            "Fit-analysis model returned non-JSON (provider=%s, model=%s); "
            "falling back to generic response.",
            settings.llm_provider, get_analysis_model(),
        )
        return JobFitAnalysis(
            analysis_summary="Analysis completed. Please review the job details for alignment.",
            pros=[],
            cons=[],
        )

    return JobFitAnalysis(
        analysis_summary=analysis_data.get("analysis_summary", "Analysis completed"),
        pros=analysis_data.get("pros", []),
        cons=analysis_data.get("cons", []),
    )
