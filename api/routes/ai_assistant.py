"""
KORRA AI - AI Assistant Route
==============================
Groq free-tier LLM for measurement insights (llama-3.3-70b-versatile).
Static fallback when no GROQ_API_KEY configured.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter()
logger = logging.getLogger("KORRA_AI")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class AssistRequest(BaseModel):
    prompt: str
    measurements: Optional[dict] = None
    body_shape: Optional[str] = None
    size_recommendation: Optional[str] = None
    height: Optional[float] = None
    gender: Optional[str] = None


def _build_system_prompt() -> str:
    return (
        "You are KORRA AI, an expert body measurement assistant for tailoring and fashion. "
        "You analyze body scan measurements and provide actionable insights for clothing fit, "
        "body shape analysis, and style recommendations. "
        "Be concise, professional, and specific. Reference actual measurement values when provided. "
        "Use centimeters as the default unit. "
        "Format responses with clear structure: use bullet points for lists and short paragraphs for analysis."
    )


def _build_context(req: AssistRequest) -> str:
    parts = []
    if req.gender:
        parts.append(f"Gender: {req.gender}")
    if req.height:
        parts.append(f"Height: {req.height} cm")
    if req.body_shape:
        parts.append(f"Body shape: {req.body_shape}")
    if req.size_recommendation:
        parts.append(f"Size recommendation: {req.size_recommendation}")
    if req.measurements:
        lines = []
        for k, v in sorted(req.measurements.items()):
            if v is not None:
                lines.append(f"  {k}: {v} cm")
        if lines:
            parts.append("Measurements:\n" + "\n".join(lines))
    return "\n".join(parts)


STATIC_RESPONSES = {
    "explain": "Based on your scan data, here's a summary of your key measurements:\n\n• **Chest**: Your chest measurement provides the foundation for jacket and shirt sizing.\n• **Waist**: Determines trouser and belt sizing. The ratio between chest and waist indicates your body proportions.\n• **Hip**: Important for trouser and skirt fitting.\n• **Shoulder**: Influences jacket and coat fit across the upper body.\n\nYour body shape classification and size recommendation are derived from the proportional relationships between these measurements.",
    "clothing": "For your body proportions:\n\n• **Shirts**: Look for fits that accommodate your chest measurement while tapering at the waist if there's a significant difference.\n• **Trousers**: Size based on your waist measurement. If hip is significantly larger than waist, consider athletic or relaxed fits.\n• **Jackets**: Size based on chest. If shoulders are broad relative to chest, consider structured shoulder designs.\n• **Dresses**: Your waist-to-hip ratio determines the most flattering silhouettes.",
    "summary": "Your body scan reveals a balanced proportional profile. The relationship between your upper and lower body measurements helps determine your ideal clothing cuts and sizes. Focus on fit at the key measurement points rather than just the size label.",
}


@router.post("/ai/assist")
async def assist(req: AssistRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    prompt_lower = req.prompt.lower()

    if not GROQ_API_KEY:
        if any(w in prompt_lower for w in ["explain", "summary", "what"]):
            response = STATIC_RESPONSES["explain"]
        elif any(w in prompt_lower for w in ["clothing", "fit", "wear", "dress", "shirt"]):
            response = STATIC_RESPONSES["clothing"]
        else:
            response = STATIC_RESPONSES["summary"]
        return {"response": response, "model": "static-fallback"}

    context = _build_context(req)
    system = _build_system_prompt()
    user_msg = f"{context}\n\nUser question: {req.prompt}" if context else req.prompt

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            )
            if res.status_code != 200:
                logger.warning("Groq API error %d: %s", res.status_code, res.text[:200])
                return {"response": STATIC_RESPONSES["summary"], "model": "static-fallback"}
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return {"response": content, "model": GROQ_MODEL}
    except Exception as e:
        logger.error("AI assist error: %s", e)
        return {"response": STATIC_RESPONSES["summary"], "model": "static-fallback"}
