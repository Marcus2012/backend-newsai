"""
Gemini AI Service - Article generation using Google Gemini 2.5 Pro
"""
import google.generativeai as genai
import json
from typing import Optional

from app.core.config import settings


# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


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
        model = genai.GenerativeModel("gemini-2.5-pro")
        prompt = build_generation_prompt(context)
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
        raise Exception(f"Error en generación con Gemini: {str(e)}")
