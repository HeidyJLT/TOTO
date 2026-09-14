"""
core/tools.py — Herramientas del agente
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Reúne las herramientas del agente TOTO:
  - fecha_hora_actual  (Sesión 2-3)
  - buscar_documentos  (RAG sobre los PDFs institucionales — Sesión 4)
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool

from core.rag import obtener_motor


@tool
def fecha_hora_actual(zona: str = "America/Bogota") -> str:
    """Devuelve la fecha y hora actual. Úsala cuando pregunten qué hora o qué día es."""
    try:
        now = datetime.now(ZoneInfo(zona))
        return now.strftime(f"%A %d de %B de %Y, %H:%M en {zona}")
    except Exception:
        return datetime.now().strftime("%A %d de %B de %Y, %H:%M")


@tool
def buscar_documentos(pregunta: str) -> str:
    """
    Busca en los documentos institucionales de la Universidad Santo Tomás
    que respaldan la construcción de aulas virtuales: el PEI, el Modelo
    Educativo Pedagógico, el Método Prudencial Santoto, los Lineamientos
    para el Diseño Curricular, las guías para redactar competencias,
    resultados de aprendizaje, preguntas orientadoras y metodología, la
    creación de rúbricas, la taxonomía de Bloom, estrategias y actividades
    didácticas, y los procedimientos de apertura y gestión de aulas del
    Campus Virtual. Úsala para cualquier pregunta sobre lineamientos
    institucionales, procesos del Campus Virtual o fundamentos pedagógicos
    de la USTA.
    """
    motor = obtener_motor()
    texto, fuentes = motor.buscar(pregunta)
    if not texto:
        return "No se encontró información relevante en los documentos institucionales."
    return texto + "\n\nFuentes consultadas: " + ", ".join(fuentes)


# ✏️ MODIFICA AQUÍ: agrega o quita herramientas del agente conversacional
TOOLS_BASE = [fecha_hora_actual, buscar_documentos]
