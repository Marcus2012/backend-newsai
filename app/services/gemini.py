"""
Gemini AI Service - Article generation using Google Gemini 2.5 Pro
"""
import google.generativeai as genai
import json
from typing import Optional

from app.core.config import settings


# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def _list_available_models() -> list:
    """Try to list available Gemini models; return list of model names or empty list."""
    try:
        if hasattr(genai, "list_models"):
            resp = genai.list_models()
            # resp may be a mapping or object
            if isinstance(resp, dict):
                return [m.get("name") for m in resp.get("models", []) if m.get("name")]
            # try attribute access
            if hasattr(resp, "models"):
                return [m.name for m in resp.models if hasattr(m, "name")]
            # fallback: try to iterate
            return list(resp)
    except Exception:
        return []


def _choose_model() -> str:
    """Choose a Gemini model to use: prefer configured one, otherwise pick a common supported model."""
    preferred = getattr(settings, "GEMINI_MODEL", None) or None
    available = _list_available_models()

    if preferred and (not available or preferred in available):
        return preferred

    # common candidates (order of preference)
    candidates = ["gemini-2.5-pro", "gemini-1.5", "gemini-1.5-pro", "gemini-pro", "gemini-1.0"]
    for c in candidates:
        if c in available:
            return c

    # fallback to preferred or a safe default
    return preferred or "gemini-1.0"


def _local_fallback_generation(context: str, raw_title: Optional[str] = None) -> dict:
    """Lightweight local generator used when Gemini is unavailable.

    Creates a safe JSON using simple heuristics from the scraped context.
    """
    # Title
    title = (raw_title or "").strip() or (context.splitlines()[0].strip() if context else "Noticia")

    # Description: first 2 sentences
    sentences = [s.strip() for s in context.replace("\n", " ").split('.') if s.strip()]
    description = ". ".join(sentences[:2])
    if description and not description.endswith('.'):
        description = description + '.'

    # SEO
    meta_title = title[:60]
    meta_description = (description[:157] + '...') if len(description) > 160 else description

    # Simple keywords: top words from title/context
    text = (title + ' ' + description).lower()
    words = [w.strip('.,"\'`()[]') for w in text.split() if len(w) > 3]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    keywords = sorted(freq.keys(), key=lambda k: -freq[k])[:5]

    return {
        "title": title,
        "description": description or "",
        "seo": {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "keywords": keywords
        }
    }


SYSTEM_PROMPT = """Eres un redactor profesional especializado en noticias. 
Tu tarea es procesar información de artículos scrapeados y generar contenido único y original.
Debes ser objetivo, imparcial y usar tono periodístico profesional.
NO inventes hechos que no estén en el contexto proporcionado.
Responde ÚNICAMENTE en formato JSON válido, sin explicaciones adicionales."""


def build_generation_prompt(context: str) -> str:
    """
    Build the prompt for Gemini with the extracted context
    
    Args:
        context: Scraped article context
    
    Returns:
        Formatted prompt string
    """
    return f"""{SYSTEM_PROMPT}

Usando EXCLUSIVAMENTE la información del CONTEXTO que sigue, genera un JSON con SOLO estos campos:

{{
  "title": "Título conciso (máx 100 caracteres)",
  "description": "Descripción en 2-3 oraciones (máx 300 caracteres)",
  "seo": {{
    "meta_title": "Meta title para SEO (máx 60 caracteres)",
    "meta_description": "Meta description para SEO (máx 160 caracteres)",
    "keywords": ["palabra1", "palabra2", "palabra3", "palabra4", "palabra5"]
  }}
}}

REGLAS CRÍTICAS:
- NO agregues información nueva o especulativa
- NO cites directamente texto del contexto (reescribe con tus palabras)
- La descripción debe ser atractiva pero fiel a los hechos
- Los keywords deben ser relevantes al tema
- Responde SOLO con el JSON, sin markdown o explicaciones

CONTEXTO A PROCESAR:
{context}

Respuesta (JSON válido únicamente):"""


async def generate_article(context: str, raw_title: Optional[str] = None) -> dict:
    """
    Generate article content using Gemini 2.5 Pro
    
    Args:
        context: Scraped article context
        raw_title: Original scraped title (optional)
    
    Returns:
        Dictionary with title, description and SEO metadata
    
    Raises:
        ValueError: If Gemini returns invalid JSON
        Exception: For other API errors
    """
    try:
        model_name = _choose_model()
        model = genai.GenerativeModel(model_name)
        prompt = build_generation_prompt(context)

        # Use synchronous generate_content when possible; some SDK versions expose async variants
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except AttributeError:
            # Older/newer SDKs may have different method names; try generate or generate_text
            if hasattr(model, "generate"):
                response = model.generate(prompt)
                response_text = getattr(response, "text", str(response)).strip()
            else:
                # Last resort: fallback to local generator
                return _local_fallback_generation(context, raw_title)
        
        # Clean markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate structure
        required_fields = ["title", "description", "seo"]
        if not all(k in result for k in required_fields):
            raise ValueError("JSON faltando campos requeridos")
        
        return result
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini retornó JSON inválido: {str(e)}")
    
    except Exception as e:
        # If model not found or 404-like errors, fallback to local generation
        msg = str(e).lower()
        if "not found" in msg or "404" in msg or ("model" in msg and "not" in msg):
            try:
                return _local_fallback_generation(context, raw_title)
            except Exception:
                raise Exception(f"Gemini error and local fallback failed: {str(e)}")
        raise Exception(f"Error en generación con Gemini: {str(e)}")
