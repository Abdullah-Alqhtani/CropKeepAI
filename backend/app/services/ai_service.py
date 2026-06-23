"""Call Groq's OpenAI-compatible API for image classification and follow-up chat.

The AI identifies evidence from an image, while database services remain the
source of treatment and product recommendations.
"""

import base64
import json
import os
from pathlib import Path

from openai import OpenAI

from app.core.config import settings
from app.services.chat_example_service import format_chat_examples, retrieve_chat_examples

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _client() -> OpenAI:
    # Groq accepts the OpenAI client format when its compatible base URL is supplied.
    return OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=_groq_api_key(),
    )


def _groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY") or settings.groq_api_key


def _load_image_data_url(path: str, content_type: str) -> str:
    # The vision request sends the saved image as a base64 data URL.
    encoded = base64.b64encode(Path(path).read_bytes()).decode("utf-8")
    return f"data:{content_type};base64,{encoded}"


def diagnose_crop_image(image_path: str, content_type: str, knowledge_context: str) -> dict:
    # Refuse the request clearly when no AI key is configured; the route can use fallback behavior.
    if not _groq_api_key():
        raise RuntimeError("GROQ_API_KEY is not configured.")

    prompt = f"""
You are CropKeepAI's crop disease diagnosis engine.

Return ONLY valid JSON. Do not include markdown, code fences, comments, prose, or any
text before or after the JSON object.

Use exactly this JSON shape:
{{
  "crop": "string",
  "disease": "string",
  "confidence": "Low | Medium | High",
  "symptoms": ["string"],
  "tags": ["string"]
}}

Rules:
- Analyze the uploaded plant/crop image and identify only the crop, disease, visible symptoms, and evidence tags.
- Do not generate treatment, prevention, product, chemical, or management recommendations.
- Do not use retrieved knowledge to invent a disease if the image does not support it.
- If the image is unclear or you are unsure, still return valid JSON.
- If unsure, set "crop" or "disease" to "Unknown" and "confidence" to "Low".
- Tags must describe visible crop/disease/symptom evidence from this image, such as crop name, lesion type, mildew, rust, blight, spots, yellowing, or wilting.
- Keep every array as an array of strings, even if there is only one item.
- Never return diagnosis text outside the JSON object.

Retrieved knowledge:
{knowledge_context}
"""
    # The strict prompt asks the model for machine-readable evidence only.
    response = _client().chat.completions.create(
        model=settings.groq_vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _load_image_data_url(image_path, content_type)}},
                ],
            }
        ],
        temperature=0,
    )
    return _parse_diagnosis_json(_message_content(response))


def answer_followup(question: str, diagnosis_context: str, knowledge_context: str, conversation: list[dict]) -> str:
    if not _groq_api_key():
        raise RuntimeError("GROQ_API_KEY is not configured.")

    history = "\n".join(f"{item['role']}: {item['content']}" for item in conversation[-8:])
    examples = retrieve_chat_examples(question, f"{diagnosis_context}\n{knowledge_context}\n{history}")
    example_context = format_chat_examples(examples)
    prompt = f"""
You are CropKeepAI's agricultural assistant. Answer the farmer's follow-up question using
the diagnosis context and knowledge base. Be practical, concise, and safety-aware.

Use the reference chat examples to match the expected customer-service behavior:
- warm, patient, direct, and service-oriented
- ask for missing order/product/crop details when needed
- give step-by-step usage guidance when the question is about dosage or application
- for refunds/logistics, explain the process and evidence needed
- for pesticide safety, do not overpromise; follow labels, intervals, PPE, and local regulations
- do not copy unsafe or incorrect claims from examples

Relevant reference examples:
{example_context}

Diagnosis:
{diagnosis_context}

Knowledge:
{knowledge_context}

Recent conversation:
{history}

Question:
{question}
"""
    response = _client().chat.completions.create(
        model=settings.groq_text_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return _message_content(response)


def select_products_from_catalog(diagnosis: dict, products: list[dict], limit: int = 5) -> list[dict]:
    if not _groq_api_key():
        raise RuntimeError("GROQ_API_KEY is not configured.")

    prompt = f"""
You are CropKeepAI's product selector.

Return ONLY valid JSON. Do not include markdown, code fences, comments, prose, or any
text before or after the JSON object.

Use exactly this JSON shape:
{{
  "recommendations": [
    {{
      "product_id": 123,
      "reason": "string",
      "usage_note": "string",
      "safety_note": "string"
    }}
  ],
  "message": "string"
}}

Rules:
- Choose products ONLY from the provided product list by product_id.
- Do not invent product names, product IDs, active ingredients, usage, or safety notes.
- Select at most {limit} products.
- If no product is suitable, return "recommendations": [] and a concise user-friendly message.
- Prefer products whose target diseases, crops, tags, active ingredient, and usage match the diagnosis.
- Do not recommend disease-specific products when the diagnosis disease is Unknown.

Diagnosis:
{json.dumps(diagnosis, ensure_ascii=False)}

Available products:
{json.dumps(products, ensure_ascii=False)}
"""
    response = _client().chat.completions.create(
        model=settings.groq_text_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    payload = json.loads(_extract_json_text(_message_content(response)))
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        return []
    return recommendations[:limit]


def _message_content(response) -> str:
    message = response.choices[0].message
    content = message.content
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return content or ""


def _parse_diagnosis_json(text: str) -> dict:
    cleaned = _extract_json_text(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        print("Raw Groq diagnosis response was not valid JSON:", text, flush=True)
        raise RuntimeError("The Groq AI response is not valid diagnosis JSON. Please retry with a clearer image.") from exc

    normalized = _normalize_required_shape(data)
    return {
        "crop_type": normalized["crop"],
        "disease_name": normalized["disease"],
        "confidence": normalized["confidence"],
        "severity": "Unknown",
        "description": "Unknown",
        "causes": "Unknown",
        "symptoms": "\n".join(normalized["symptoms"]),
        "tags": normalized["tags"],
        "impact": "Unknown",
        "treatment_steps": "Unknown",
        "preventive_actions": "Unknown",
        "environmental_considerations": "Follow local weather, label, and safety guidance.",
    }


def _extract_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return cleaned


def _normalize_required_shape(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    confidence = str(data.get("confidence") or "Low").strip().title()
    if confidence not in {"Low", "Medium", "High"}:
        confidence = "Low"
    return {
        "crop": _string_value(data.get("crop")),
        "disease": _string_value(data.get("disease")),
        "confidence": confidence,
        "symptoms": _string_list(data.get("symptoms")),
        "tags": _string_list(data.get("tags")),
    }


def _string_value(value) -> str:
    if value is None:
        return "Unknown"
    value = str(value).strip()
    return value or "Unknown"


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif value:
        items = [str(value).strip()]
    else:
        items = []
    return items or ["Unknown"]
