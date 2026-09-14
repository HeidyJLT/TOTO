"""
core/graph.py — Grafo coordinador (LangGraph)
TOTO — asesor de aulas virtuales de la Universidad Santo Tomás Bucaramanga

Este es el "cerebro" del agente: el COORDINADOR lee la pregunta del
docente y decide solo cuál camino tomar.

      START → coordinador → [conversacion | consulta | asesoria | insumo] → END

  • conversacion → agente con memoria + herramientas         (Sesiones 1-3)
  • consulta     → RAG sobre los documentos institucionales   (Sesión 4)
  • asesoria     → equipo Rastreador→Asesor pedagógico→Redactor (Sesión 4)
  • insumo       → Salida Estructurada con Pydantic            (Sesión 2)

✏️ MODIFICA AQUÍ: ajusta las categorías, los prompts o agrega un
   nuevo camino siguiendo el mismo patrón.
"""

import os
import sys
from typing import TypedDict, Literal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END

from s6_llm_factory import crear_llm
from core.tools import TOOLS_BASE, buscar_documentos
from core.rag import obtener_motor
from core.structured import InsumoAula

NOMBRE_AGENTE = os.getenv("AGENT_NAME", "Asistente")
ROL_AGENTE = os.getenv("AGENT_ROLE", "asistente de la Universidad Santo Tomás")

ALCANCE_AGENTE = """Acompañas a los docentes de la Universidad Santo Tomás, \
seccional Bucaramanga, en la construcción de sus aulas virtuales. Tus temas \
son: competencias, resultados de aprendizaje, taxonomía de Bloom, \
actividades evaluativas, rúbricas, estrategias didácticas, recursos \
educativos digitales, y los lineamientos y procedimientos institucionales \
del Campus Virtual.

Te apoyas en la documentación institucional cargada y citas el documento \
del que sale cada afirmación. NO inventas lineamientos, cifras, normas ni \
procedimientos que no estén en esa documentación. SÍ puedes aplicar los \
criterios institucionales al caso concreto del docente cuando te pida \
construir algo (una rúbrica, un resultado de aprendizaje, una actividad \
evaluativa) — eso no es inventar: es aplicar.

Ante un tema ajeno a tu alcance (cálculos, consultas generales, temas no \
académicos), lo dices con claridad y reencauzas la conversación hacia lo \
que sí puedes hacer, sin intentar responderlo."""

MENSAJE_SIN_INFO = (
    "No encuentro esa información en la documentación institucional que "
    "tengo disponible. Puedo acompañarte en el diseño de competencias, "
    "resultados de aprendizaje, actividades evaluativas, rúbricas y "
    "estrategias didácticas para tu aula virtual. Si necesitas ese dato "
    "puntual, te sugiero consultarlo con el Departamento de Educación "
    "Virtual de la seccional."
)


def _modelo_clasificador() -> str | None:
    """Modelo liviano para el nodo coordinador, según el proveedor activo."""
    proveedor = os.getenv("LLM_PROVIDER", "ollama")
    if proveedor == "groq":
        return os.getenv("GROQ_MODEL_CLASIFICADOR") or None
    return os.getenv("OLLAMA_MODEL_CLASIFICADOR") or None


def _max_tokens_clasificador() -> int:
    """Tope de tokens para el nodo coordinador, según el proveedor activo."""
    proveedor = os.getenv("LLM_PROVIDER", "ollama")
    if proveedor == "groq":
        return int(os.getenv("GROQ_MAX_TOKENS_CLASIFICADOR", "512"))
    return int(os.getenv("OLLAMA_MAX_TOKENS_CLASIFICADOR", "8"))


def limpiar_pensamiento(texto: str) -> str:
    """
    Algunos modelos 'razonadores' (ej. qwen3.6) anteponen un bloque
    <think>...</think> con su razonamiento interno antes de la
    respuesta final. Nos quedamos solo con lo que viene después.
    """
    if texto and "</think>" in texto:
        return texto.split("</think>")[-1].strip()
    return (texto or "").strip()


# ═══════════════════════════════════════════════════════════
#  STATE — el diccionario compartido entre todos los nodos
# ═══════════════════════════════════════════════════════════
class EstadoAgente(TypedDict):
    entrada_usuario: str
    historial: list
    categoria: str
    respuesta_final: str
    fuentes: list


# ═══════════════════════════════════════════════════════════
#  COORDINADOR — clasifica y decide el camino (edge condicional)
# ═══════════════════════════════════════════════════════════
def nodo_coordinador(estado: EstadoAgente) -> dict:
    llm = crear_llm(temperature=0.0, max_tokens=_max_tokens_clasificador(), modelo=_modelo_clasificador())
    instrucciones = """Clasifica la pregunta del docente en UNA categoría:
- consulta: pregunta puntual sobre lineamientos, políticas o procedimientos
  institucionales de la Universidad Santo Tomás (PEI, modelo pedagógico,
  método prudencial, procesos del Campus Virtual).
- asesoria: el docente pide ayuda para construir, revisar o mejorar algo
  pedagógico en profundidad (diseñar una estrategia didáctica, redactar
  mejor una competencia, evaluar si una actividad está bien alineada).
- insumo: el docente pide explícitamente generar el insumo estructurado
  de aula (competencia, resultados de aprendizaje, nivel de la taxonomía
  de Bloom, actividad evaluativa y criterios de rúbrica).
- conversacion: cualquier otra cosa (saludos, cálculos, hora, preguntas
  generales no pedagógicas).

Responde SOLO con la categoría, en minúsculas, sin explicación ni puntuación.

Ejemplos:
"¿Qué dice el PEI sobre la formación integral?" -> consulta
"¿Cuál es el proceso para abrir un aula virtual?" -> consulta
"¿Qué es el Método Prudencial Santoto?" -> consulta
"¿Qué establecen los lineamientos de diseño curricular sobre las aulas de acompañamiento?" -> consulta
"Ayúdame a diseñar una estrategia didáctica para mi curso de estadística" -> asesoria
"Revisa si mi actividad evaluativa está alineada con la competencia del curso" -> asesoria
"Quiero mejorar la redacción de mis resultados de aprendizaje" -> asesoria
"Genera el insumo de aula para mi curso de Contabilidad II" -> insumo
"Necesito la competencia, los resultados de aprendizaje y la rúbrica para mi asignatura" -> insumo
"Arma la ficha de insumo con nivel de Bloom y actividad evaluativa" -> insumo
"Hola, ¿cómo estás?" -> conversacion
"¿Cuánto es 45 * 12?" -> conversacion
"¿Qué hora es en Bogotá?" -> conversacion"""
    resp = llm.invoke([
        SystemMessage(content=instrucciones),
        HumanMessage(content=estado["entrada_usuario"]),
    ])
    contenido = limpiar_pensamiento(resp.content).lower()

    categoria = None
    for opcion in ("consulta", "insumo", "asesoria", "conversacion"):
        if opcion in contenido:
            categoria = opcion
            break

    if categoria is None:
        print(f"  ⚠️  [COORDINADOR] Ninguna categoría reconocida, uso 'conversacion' por defecto. Respuesta cruda del modelo: {resp.content!r}")
        categoria = "conversacion"
    else:
        print(f"  🎯 [COORDINADOR] → {categoria.upper()}")

    return {"categoria": categoria}


def router(estado: EstadoAgente) -> Literal["conversacion", "consulta", "asesoria", "insumo"]:
    return estado.get("categoria", "conversacion")


# ═══════════════════════════════════════════════════════════
#  NODO: CONVERSACIÓN — agente con memoria + herramientas
# ═══════════════════════════════════════════════════════════
def nodo_conversacion(estado: EstadoAgente) -> dict:
    llm = crear_llm()
    system_prompt = f"""Eres {NOMBRE_AGENTE}, un {ROL_AGENTE}.
{ALCANCE_AGENTE}

Responde siempre en español, claro y directo.
Usa tus herramientas cuando las necesites en vez de inventar datos."""
    agente = create_agent(model=llm, tools=TOOLS_BASE, system_prompt=system_prompt)
    resultado = agente.invoke({
        "messages": estado["historial"] + [HumanMessage(content=estado["entrada_usuario"])]
    })
    return {"respuesta_final": limpiar_pensamiento(resultado["messages"][-1].content)}


# ═══════════════════════════════════════════════════════════
#  NODO: CONSULTA — RAG sobre los documentos institucionales
# ═══════════════════════════════════════════════════════════
def nodo_consulta(estado: EstadoAgente) -> dict:
    motor = obtener_motor()
    contexto, fuentes = motor.buscar(estado["entrada_usuario"])

    llm = crear_llm(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Eres {NOMBRE_AGENTE}, {ROL_AGENTE}.
{ALCANCE_AGENTE}

Responde ÚNICAMENTE basándote en el contexto de los documentos
institucionales proporcionado. Si la información no está en el contexto,
responde EXACTAMENTE con este mensaje, sin agregar nada más:
"{MENSAJE_SIN_INFO}"
Cita el archivo/página cuando sea posible. Responde en español, claro y
profesional."""),
        ("human", "Contexto de los documentos institucionales:\n{contexto}\n\nPregunta: {pregunta}"),
    ])
    chain = prompt | llm | StrOutputParser()
    respuesta = chain.invoke({
        "contexto": contexto or "(no se encontró contexto relevante)",
        "pregunta": estado["entrada_usuario"],
    })
    return {"respuesta_final": limpiar_pensamiento(respuesta), "fuentes": fuentes}


# ═══════════════════════════════════════════════════════════
#  NODO: ASESORÍA — equipo Rastreador de lineamientos → Asesor
#  pedagógico → Redactor
# ═══════════════════════════════════════════════════════════
def nodo_asesoria(estado: EstadoAgente) -> dict:
    print("  🔍 [RASTREADOR DE LINEAMIENTOS] Recopilando lineamientos institucionales...")
    agente_rastreador = create_agent(
        model=crear_llm(temperature=0.3),
        tools=[buscar_documentos],
        system_prompt=f"""Eres un rastreador de lineamientos institucionales.
{ALCANCE_AGENTE}

Usa tus herramientas para recopilar los lineamientos, criterios y
procedimientos reales de la USTA relevantes a la pregunta ANTES de
concluir nada. Sé concreto. Responde en español, en lista de puntos clave.""",
    )
    lineamientos = limpiar_pensamiento(agente_rastreador.invoke({
        "messages": [HumanMessage(content=f"Rastrea lineamientos sobre: {estado['entrada_usuario']}")]
    })["messages"][-1].content)

    print("  🎓 [ASESOR PEDAGÓGICO] Analizando y asesorando...")
    asesoria = limpiar_pensamiento(crear_llm(temperature=0.4).invoke([
        SystemMessage(content=f"""Eres un asesor pedagógico de la Universidad
Santo Tomás. {ALCANCE_AGENTE}

Interpreta los lineamientos recopilados y da recomendaciones concretas y
accionables para el docente, alineadas al modelo educativo pedagógico de
la USTA. Si los lineamientos recopilados no cubren la pregunta del
docente, responde EXACTAMENTE con este mensaje, sin agregar nada más:
"{MENSAJE_SIN_INFO}"
Responde en español, estructurado."""),
        HumanMessage(content=f"Pregunta del docente: {estado['entrada_usuario']}\n\n"
                              f"Lineamientos recopilados:\n{lineamientos}\n\nAnaliza y asesora."),
    ]).content)

    print("  ✍️  [REDACTOR] Redactando respuesta final...")
    redaccion = limpiar_pensamiento(crear_llm(temperature=0.5).invoke([
        SystemMessage(content=f"""Eres {NOMBRE_AGENTE}. {ALCANCE_AGENTE}

Toma la asesoría pedagógica recibida y conviértela en una respuesta final
clara y bien organizada para el docente. Si la asesoría indica que no se
encontró información, conserva ese mensaje tal cual, sin inventar
contenido adicional. Responde en español."""),
        HumanMessage(content=f"Pregunta original: {estado['entrada_usuario']}\n\n"
                              f"Asesoría pedagógica:\n{asesoria}\n\nRedacta la respuesta final."),
    ]).content)

    return {"respuesta_final": redaccion}


# ═══════════════════════════════════════════════════════════
#  NODO: INSUMO — Salida Estructurada con Pydantic
# ═══════════════════════════════════════════════════════════
def nodo_insumo(estado: EstadoAgente) -> dict:
    # ✏️ Algunos modelos (ej. qwen3.6) fallan con with_structured_output
    # ("tool_use_failed"). GROQ_MODEL_ESTRUCTURADO permite usar un
    # modelo distinto solo para este nodo cuando el proveedor es Groq.
    # Con Ollama se respeta el modelo configurado en OLLAMA_MODEL.
    proveedor = os.getenv("LLM_PROVIDER", "ollama")
    modelo_estructurado = os.getenv("GROQ_MODEL_ESTRUCTURADO") if proveedor == "groq" else None
    llm_estructurado = crear_llm(temperature=0.4, modelo=modelo_estructurado).with_structured_output(InsumoAula)

    motor = obtener_motor()
    contexto, _fuentes = motor.buscar(estado["entrada_usuario"])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""{ALCANCE_AGENTE}

Genera el insumo de aula para el docente, basándote en los lineamientos
institucionales disponibles (rúbricas, taxonomía de Bloom, diseño
curricular). Sé específico y accionable. Responde en español."""),
        ("human", "Solicitud: {solicitud}\n\nLineamientos institucionales disponibles:\n{datos}"),
    ])
    chain = prompt | llm_estructurado
    insumo: InsumoAula = chain.invoke({
        "solicitud": estado["entrada_usuario"],
        "datos": contexto or "(no se encontraron lineamientos específicos en el contexto; apóyate únicamente en los criterios institucionales generales de la USTA que sí conozcas de la documentación cargada, sin fabricar normas, cifras ni procedimientos que no aparezcan en ella)",
    })

    salida = f"📋 INSUMO DE AULA\n\nCompetencia: {insumo.competencia}\n"
    if insumo.resultados_aprendizaje:
        salida += "\nRESULTADOS DE APRENDIZAJE:\n" + "\n".join(f"  • {r}" for r in insumo.resultados_aprendizaje) + "\n"
    salida += f"\nNIVEL TAXONOMÍA DE BLOOM: {insumo.nivel_bloom}\n"
    salida += f"\nACTIVIDAD EVALUATIVA:\n{insumo.actividad_evaluativa}\n"
    if insumo.criterios_rubrica:
        salida += "\nCRITERIOS DE RÚBRICA:\n"
        for c in insumo.criterios_rubrica:
            salida += f"  • [{c.criterio}] {c.descripcion} — Nivel de logro: {c.nivel_logro}\n"

    return {"respuesta_final": salida}


# ═══════════════════════════════════════════════════════════
#  CONSTRUCCIÓN DEL GRAFO
# ═══════════════════════════════════════════════════════════
def construir_grafo():
    grafo = StateGraph(EstadoAgente)

    grafo.add_node("coordinador", nodo_coordinador)
    grafo.add_node("conversacion", nodo_conversacion)
    grafo.add_node("consulta", nodo_consulta)
    grafo.add_node("asesoria", nodo_asesoria)
    grafo.add_node("insumo", nodo_insumo)

    grafo.add_edge(START, "coordinador")
    grafo.add_conditional_edges("coordinador", router, {
        "conversacion": "conversacion",
        "consulta": "consulta",
        "asesoria": "asesoria",
        "insumo": "insumo",
    })
    grafo.add_edge("conversacion", END)
    grafo.add_edge("consulta", END)
    grafo.add_edge("asesoria", END)
    grafo.add_edge("insumo", END)

    return grafo.compile()
