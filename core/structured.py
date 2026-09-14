"""
core/structured.py — Esquemas Pydantic para Salida Estructurada
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Mismo concepto de la Sesión 2 (Structured Output): en vez de dejar
que el modelo redacte libremente, le damos un "formulario" con
casillas fijas que tiene que llenar siempre igual.
"""

from typing import List
from pydantic import BaseModel, Field


class CriterioRubrica(BaseModel):
    """Un criterio de la rúbrica de evaluación de la actividad."""
    criterio: str = Field(description="Nombre del criterio evaluado, ej. 'Claridad conceptual'")
    descripcion: str = Field(description="Qué se evalúa en este criterio")
    nivel_logro: str = Field(description="Nivel de logro esperado, ej. 'Sobresaliente', 'Aceptable', 'Insuficiente'")


class InsumoAula(BaseModel):
    """Insumo estructurado para la construcción de un aula virtual."""
    competencia: str = Field(description="Competencia a desarrollar en el curso")
    resultados_aprendizaje: List[str] = Field(default_factory=list, description="Resultados de aprendizaje asociados a la competencia")
    nivel_bloom: str = Field(description="Nivel de la taxonomía de Bloom: Recordar, Comprender, Aplicar, Analizar, Evaluar o Crear")
    actividad_evaluativa: str = Field(description="Actividad evaluativa propuesta para el resultado de aprendizaje")
    criterios_rubrica: List[CriterioRubrica] = Field(default_factory=list, description="Criterios de la rúbrica de evaluación de la actividad")
