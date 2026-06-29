"""
KORRA AI - AI Assistant Route
==============================
Groq free-tier LLM for measurement insights (llama-3.3-70b-versatile).
Full dashboard context: measurements, scan history, attire, chat history.
Static fallback when no GROQ_API_KEY configured.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

router = APIRouter()
logger = logging.getLogger("KORRA_AI")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


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

    messages = [{"role": "system", "content": system}]

    if req.chat_history:
        for msg in req.chat_history[-8:]:
            if msg.role in ("user", "assistant") and msg.content:
                messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 600,
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
