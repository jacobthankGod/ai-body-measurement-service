"""
KORRA AI - AI Assistant Route
==============================
Multi-provider LLM fallback chain for measurement insights.
Priority: Groq -> OpenRouter -> Google Gemini -> Mistral -> Static fallback.
Full dashboard context: measurements, scan history, attire, chat history.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

router = APIRouter()
logger = logging.getLogger("KORRA_AI")

# ═══ PROVIDER CONFIG ═══
# Set API keys as environment variables. Only Groq is required; others are optional fallbacks.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

PROVIDERS = [
    {
        "name": "groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "api_key": GROQ_API_KEY,
        "timeout": 15.0,
    },
    {
        "name": "openrouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "google/gemma-4-31b-it:free",
        "api_key": OPENROUTER_API_KEY,
        "timeout": 20.0,
        "extra_headers": {
            "HTTP-Referer": "https://korra.work",
            "X-Title": "KORRA AI",
        },
    },
    {
        "name": "gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
        "api_key": GEMINI_API_KEY,
        "timeout": 20.0,
    },
    {
        "name": "mistral",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-small-latest",
        "api_key": MISTRAL_API_KEY,
        "timeout": 20.0,
    },
]


class ChatMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ScanSnapshot(BaseModel):
    date: Optional[str] = None
    measurements: Optional[dict] = None
    body_shape: Optional[str] = None
    size: Optional[str] = None


class AssistRequest(BaseModel):
    prompt: str
    measurements: Optional[dict] = None
    body_shape: Optional[str] = None
    size_recommendation: Optional[str] = None
    height: Optional[float] = None
    gender: Optional[str] = None
    client_name: Optional[str] = None
    scan_date: Optional[str] = None
    active_attire: Optional[str] = None
    active_material: Optional[str] = None
    show_eased: Optional[bool] = None
    selected_measurement: Optional[str] = None
    unit_preference: Optional[str] = None
    notes: Optional[str] = None
    scan_history: Optional[List[ScanSnapshot]] = None
    chat_history: Optional[List[ChatMessage]] = None


ATTIRE_NAMES = {
    "standard": "Standard daily wear",
    "agbada": "Agbada (flowing West African robe)",
    "senator": "Senator suit (fitted Nigerian style)",
    "kurta": "Kurta (South Asian tunic)",
    "kaftan": "Kaftan (loose robe)",
    "abaya": "Abaya (overgarment)",
    "activewear": "Activewear / sportswear",
    "isi_agu": "Isi Agu (Igbo ceremonial)",
    "bespoke_suit": "Bespoke suit",
    "savile_row": "Savile Row suit",
    "kilt": "Scottish kilt",
    "hanbok": "Korean hanbok",
    "ao_dai": "Vietnamese Ao Dai",
    "kimono": "Japanese kimono",
    "sari": "Indian sari",
    "lehenga": "Indian lehenga",
    "barong_tagalog": "Filipino Barong",
    "thobe_kandura": "Thobe / Kandura",
    "swimwear": "Swimwear",
    "denim": "Denim",
    "streetwear": "Streetwear",
}

MATERIAL_NAMES = {
    "woven": "woven (standard structure)",
    "knit": "knit (stretchy, form-fitting)",
    "starch_bazin": "starch bazin (stiff, structured)",
    "technical": "technical (performance fabric)",
}


def _build_system_prompt() -> str:
    return (
        "You are KORRA AI, an expert body measurement assistant for tailoring and fashion. "
        "You have access to the user's full body scan data, measurement history, "
        "active garment context, fabric type, and conversation history. "
        "You analyze body scan measurements and provide actionable insights for clothing fit, "
        "body shape analysis, style recommendations, and measurement progress tracking.\n\n"
        "Key capabilities:\n"
        "- Reference actual measurement values from the scan data\n"
        "- When scan history is provided, compare current vs previous measurements and note trends\n"
        "- When an active attire context is provided, tailor advice to that garment type's specific fit requirements\n"
        "- When fabric type is provided, adjust recommendations (knit stretches, starch bazin is stiff, etc.)\n"
        "- When user notes are provided, acknowledge and reference them\n"
        "- When the user is viewing a specific measurement, focus on that area\n"
        "- If garment mode is on (show_eased), explain that values include ease for the selected attire\n"
        "- Use centimeters as default unless the user prefers inches\n\n"
        "Be concise, professional, and specific. "
        "Format responses with clear structure: bullet points for lists, short paragraphs for analysis. "
        "Keep responses under 200 words unless the user asks for detail."
    )


def _build_context(req: AssistRequest) -> str:
    parts = []

    if req.client_name:
        parts.append(f"Client: {req.client_name}")
    if req.gender:
        parts.append(f"Gender: {req.gender}")
    if req.height:
        parts.append(f"Height: {req.height} cm")
    if req.body_shape:
        parts.append(f"Body shape: {req.body_shape}")
    if req.size_recommendation:
        parts.append(f"Size recommendation: {req.size_recommendation}")
    if req.scan_date:
        parts.append(f"Scan date: {req.scan_date}")

    if req.active_attire and req.active_attire != 'standard':
        attire_label = ATTIRE_NAMES.get(req.active_attire, req.active_attire.replace('_', ' ').title())
        parts.append(f"Active attire context: {attire_label}")
    if req.active_material and req.active_material != 'woven':
        mat_label = MATERIAL_NAMES.get(req.active_material, req.active_material)
        parts.append(f"Fabric type: {mat_label}")
    if req.show_eased is not None:
        mode = "garment measurements (with ease applied)" if req.show_eased else "raw body measurements (no ease)"
        parts.append(f"Display mode: {mode}")
    if req.selected_measurement:
        parts.append(f"User is currently viewing: {req.selected_measurement}")
    if req.unit_preference and req.unit_preference != 'cm':
        parts.append(f"Preferred unit: {req.unit_preference}")
    if req.notes:
        parts.append(f"User notes on this scan: {req.notes}")

    if req.measurements:
        lines = []
        for k, v in sorted(req.measurements.items()):
            if v is not None:
                lines.append(f"  {k}: {v} cm")
        if lines:
            parts.append("Current measurements:\n" + "\n".join(lines))

    if req.scan_history:
        parts.append(f"\nScan history ({len(req.scan_history)} previous scans for this client):")
        for i, s in enumerate(req.scan_history):
            date = s.date or "unknown"
            shape = s.body_shape or "N/A"
            size = s.size or "N/A"
            parts.append(f"  Scan {i + 1} ({date}): shape={shape}, size={size}")
            if s.measurements:
                key_measurements = {
                    k: v for k, v in s.measurements.items()
                    if k in ['Chest Round', 'Waist Round', 'Hip Round', 'Shoulder', 'Thigh Round']
                }
                for k, v in key_measurements.items():
                    if v is not None:
                        parts.append(f"    {k}: {v} cm")

    return "\n".join(parts)


STATIC_RESPONSES = {
    "explain": "Based on your scan data, here's a summary of your key measurements:\n\n• **Chest**: Your chest measurement provides the foundation for jacket and shirt sizing.\n• **Waist**: Determines trouser and belt sizing. The ratio between chest and waist indicates your body proportions.\n• **Hip**: Important for trouser and skirt fitting.\n• **Shoulder**: Influences jacket and coat fit across the upper body.\n\nYour body shape classification and size recommendation are derived from the proportional relationships between these measurements.",
    "clothing": "For your body proportions:\n\n• **Shirts**: Look for fits that accommodate your chest measurement while tapering at the waist if there's a significant difference.\n• **Trousers**: Size based on your waist measurement. If hip is significantly larger than waist, consider athletic or relaxed fits.\n• **Jackets**: Size based on chest. If shoulders are broad relative to chest, consider structured shoulder designs.\n• **Dresses**: Your waist-to-hip ratio determines the most flattering silhouettes.",
    "summary": "Your body scan reveals a balanced proportional profile. The relationship between your upper and lower body measurements helps determine your ideal clothing cuts and sizes. Focus on fit at the key measurement points rather than just the size label.",
}


def _build_static_response(prompt_lower: str) -> str:
    if any(w in prompt_lower for w in ["explain", "summary", "what"]):
        return STATIC_RESPONSES["explain"]
    elif any(w in prompt_lower for w in ["clothing", "fit", "wear", "dress", "shirt"]):
        return STATIC_RESPONSES["clothing"]
    return STATIC_RESPONSES["summary"]


async def _call_provider(provider: dict, messages: list) -> Optional[str]:
    """Call a single provider. Returns response content or None on failure."""
    if not provider["api_key"]:
        return None

    headers = {"Authorization": f"Bearer {provider['api_key']}"}
    headers.update(provider.get("extra_headers", {}))

    try:
        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            res = await client.post(
                provider["url"],
                headers=headers,
                json={
                    "model": provider["model"],
                    "messages": messages,
                    "max_tokens": 600,
                    "temperature": 0.7,
                },
            )
            if res.status_code == 200:
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content:
                    logger.info("AI provider '%s' succeeded", provider["name"])
                    return content
                logger.warning("AI provider '%s' returned empty content", provider["name"])
                return None
            else:
                logger.warning("AI provider '%s' error %d: %s", provider["name"], res.status_code, res.text[:200])
                return None
    except Exception as e:
        logger.warning("AI provider '%s' exception: %s", provider["name"], str(e)[:200])
        return None


@router.post("/ai/assist")
async def assist(req: AssistRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    prompt_lower = req.prompt.lower()

    context = _build_context(req)
    system = _build_system_prompt()
    user_msg = f"{context}\n\nUser question: {req.prompt}" if context else req.prompt

    messages = [{"role": "system", "content": system}]

    if req.chat_history:
        for msg in req.chat_history[-8:]:
            if msg.role in ("user", "assistant") and msg.content:
                messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_msg})

    for provider in PROVIDERS:
        if not provider["api_key"]:
            continue
        result = await _call_provider(provider, messages)
        if result:
            return {"response": result, "model": provider["name"]}

    logger.warning("All AI providers failed, returning static fallback")
    return {"response": _build_static_response(prompt_lower), "model": "static-fallback"}
