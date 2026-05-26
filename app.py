"""
Tutor Interactivo de Oposiciones - Técnico Especialista (Opción Terapeuta) - CARM.
Aplicación Streamlit que consume la API gratuita de Google Gemini
(gemini-2.5-flash) como preparador personal. Pensada para uso doméstico.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import streamlit as st
from google import genai
from google.genai import types as genai_types


# ---------------------------------------------------------------------------
# Configuración general y constantes
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Tutor Oposiciones - Terapeuta CARM",
    page_icon="🎓",
    layout="wide",
)

MODEL_ID = "gemini-2.5-flash"
MAX_TOKENS = 8000
EXAMEN_JSON = Path(__file__).parent / "examen_data.json"

# Enunciados LITERALES extraídos del BORM (Anexo III, Orden 27 abril 2016).
TEMAS_COMUNES = [
    "Tema 1. La Constitución española de 1978: estructura y contenido. Derechos y deberes fundamentales: garantía y suspensión. Instituciones básicas del Estado. Estatuto de Autonomía de la Región de Murcia: estructuración y contenido.",
    "Tema 2. Concepto de Administración Pública. Diferentes niveles de la Administración Pública: Administración Estatal, Autonómica, Local e Institucional: ideas básicas. La Administración Pública de la Comunidad Autónoma de Murcia: organización y régimen jurídico.",
    "Tema 3. Ordenación de la Función Pública Regional. Principios informadores. Clases de personal: su régimen jurídico. Derechos y Deberes: derechos de negociación colectiva y huelga. Régimen disciplinario. Régimen de incompatibilidades. Retribuciones. La responsabilidad de las administraciones y de los funcionarios. La protección de datos de carácter personal y el secreto profesional.",
    "Tema 4. El presupuesto de la Comunidad Autónoma. Principios presupuestarios. Elaboración y aprobación del presupuesto. La ejecución del presupuesto: operaciones necesarias. Gestión de los diferentes gastos. Modificaciones presupuestarias.",
    "Tema 5. Los principios informadores de la actividad administrativa: eficacia, jerarquía, descentralización, desconcentración, coordinación y legalidad.",
    "Tema 6. El procedimiento administrativo común: concepto. Fases del procedimiento administrativo común. Audiencia al interesado. Cómputo de plazos. La revisión de los actos en vía administrativa. Los derechos de los ciudadanos.",
    "Tema 7. Los procedimientos de contratación.",
    "Tema 8. Los recursos humanos y la calidad en los servicios. Los servicios de información administrativa y de atención al ciudadano.",
    "Tema 9. Los sistemas informáticos: concepto, componentes y funcionamiento general. Redes de ordenadores e Internet. La red corporativa de la Comunidad Autónoma de la Región de Murcia.",
    "Tema 10. Prevención de riesgos laborales: derechos y obligaciones de los trabajadores en materia de prevención de riesgos laborales. La organización de la Prevención de Riesgos Laborales en la Administración Regional.",
    "Tema 11. La sede electrónica. La identificación y autenticación de las personas físicas y jurídicas para las diferentes actuaciones en la gestión electrónica. El documento electrónico. El expediente electrónico. La Plataforma de Interoperabilidad.",
    "Tema 12. Igualdad: Disposiciones generales. Transparencia y acceso a la información pública: conceptos fundamentales.",
]

# Enunciados LITERALES extraídos del BORM (Anexo, Orden 5 mayo 2014) — 35 temas.
TEMAS_ESPECIFICOS = [
    "Tema 1. Salud y enfermedad. Principios y orientaciones de la educación para la Salud. Salud y desarrollo comunitario. Concepto de pluripatología. Ergoterapia, laborterapia y terapia ocupacional. El papel de la terapia ocupacional en la salud.",
    "Tema 2. Salud laboral. Prevención de accidentes laborales. Vigilancia de factores de riesgo: técnicas de prevención. Trabajo con máquinas. Lesiones de tipo acumulativo profesional.",
    "Tema 3. Clasificación Internacional de Deficiencia, Discapacidad y Minusvalía. Definición y características. Ley 39/2006, de 14 de Diciembre, de Promoción de la Autonomía Personal y Atención a las personas en Situación de Dependencia. Procedimiento para la valoración y el reconocimiento de la Situación de Dependencia.",
    "Tema 4. La integración social y laboral de las personas con discapacidad. La inserción ocupacional. Programas de empleo con apoyo. Centros Ocupacionales. Centros Especiales de Empleo.",
    "Tema 5. Ergonomía y Discapacidad. Contribución de la ergonomía en el área de la discapacidad. Ayudas técnicas en terapia ocupacional. Análisis del trabajo. Medidas de intervención para adaptar el trabajo a personas con discapacidad.",
    "Tema 6. Accesibilidad para personas con movilidad reducida. Barreras arquitectónicas. Parámetros antropométricos. La Ley de Condiciones de Habitabilidad y Promoción de la Accesibilidad General.",
    "Tema 7. La discapacidad intelectual. Concepto, etiología y clasificación.",
    "Tema 8. Las discapacidades sensoriales. Personas ciegas o ambliopes. Personas con deficiencia auditiva.",
    "Tema 9. Las discapacidades motóricas. Tipos y clasificación. Características principales de cada una de ellas. Biomecánica.",
    "Tema 10. El autismo y otras alteraciones graves del desarrollo. Programas de comunicación alternativos. Abordaje de los problemas de conducta.",
    "Tema 11. Diagnóstico y clasificación de las enfermedades mentales. Características generales del enfermo mental crónico. La reinserción social y laboral del enfermo mental crónico. Entrenamiento en actividades para la búsqueda activa de empleo.",
    "Tema 12. Las drogodependencias: conceptos fundamentales. La reinserción social y laboral del toxicómano. Ley 6/1997, de 22 de octubre, sobre drogas, para la prevención, asistencia e integración social.",
    "Tema 13. El envejecimiento: aspectos biológicos, psicológicos y sociales de la vejez. La rehabilitación terapéutica de personas mayores. Plan de Acción Social para las Personas Mayores de la Región de Murcia. La Coordinación socio-sanitaria como base del tratamiento de atención integral a las personas mayores.",
    "Tema 14. La función del terapeuta. Su papel en el Sistema de Servicios Sociales. El terapeuta en el equipo multiprofesional. Competencias profesionales del terapeuta.",
    "Tema 15. Importancia de la relación del terapeuta con la familia del discapacitado, del enfermo mental crónico, del toxicómano y de la persona mayor.",
    "Tema 16. Real Decreto Legislativo 1/2013, de 29 de Noviembre, por el que se aprueba el Texto Refundido de la Ley General de Derechos de las Personas con Discapacidad y de su Inclusión Social.",
    "Tema 17. La formación para el empleo. La formación ocupacional. Los programas de garantía social. Empleo y discapacidad. Itinerario laboral.",
    "Tema 18. La formación profesional. Evolución de la concepción de la formación profesional. Tipos de programas y características de la formación profesional para personas con discapacidad.",
    "Tema 19. Diseño y Análisis de Tareas. Desarrollo de un curso sistemático. Destinatarios del curso. Planificación de la práctica.",
    "Tema 20. Talleres ocupacionales. Adaptación a través de la ocupación humana. Exploración prevocacional. Plan de trabajo. Talleres artísticos.",
    "Tema 21. Dinámica de un taller. Adecuación de contenidos y actividades.",
    "Tema 22. Conductas preelaborales. Conductas laborales. Seguridad. Adaptación y entrenamiento en el puesto de trabajo. Seguimiento y apoyo continuado.",
    "Tema 23. Organización de un taller. Organización del material. Maquinaria. Herramientas. Espacio y almacenaje.",
    "Tema 24. Diseño de actividades programadas y de espacios terapéuticos. Presentación de la actividad y realización del ensayo. Configuración individual de actividades. Práctica de la actividad.",
    "Tema 25. La evaluación de la formación. Clases de evaluación. Técnicas e instrumentos de evaluación. Pruebas objetivas. Evaluación de las prácticas: lista de cotejo y escala de evaluación. Valoración de programas. Diagnóstico ocupacional.",
    "Tema 26. Dinámica de grupos en la formación. La dinámica de grupos como técnica central del abordaje terapéutico. Habilidades para participar en grupos: grupos paralelos, grupos cooperativos, proyecto grupal, grupos maduros.",
    "Tema 27. Artes aplicadas, artes decorativas e industriales. Nuevas tecnologías y terapia ocupacional. La creación artística.",
    "Tema 28. Actividades manuales diversas. Actividades artesanales y artísticas.",
    "Tema 29. Desarrollo de habilidades sociales y de autonomía personal: aseo personal, atención a la alimentación, ocio y tiempo libre. Habilidades de autocuidado.",
    "Tema 30. Incremento de la productividad en el desempeño de tareas. Incremento gradual del período de trabajo.",
    "Tema 31. Retraso mental y envejecimiento. Programa de recreo, terapia expresiva y arteterapia. Dinámicas entre creación y procesos terapéuticos. Desarrollo del proceso creativo.",
    "Tema 32. El terapeuta en las actividades de la vida diaria: alimentación, higiene, cuidado personal, medicación, socialización, comunicación, movilidad funcional, respuesta a emergencias, expresión sexual y arreglo. Terapias individuales, grupales y a domicilio.",
    "Tema 33. Las organizaciones no gubernamentales y su relación con los servicios sociales. Cooperación con la Administración. El voluntariado social. Plan Estatal del Voluntariado. Ley 6/1996, de 15 de enero del Voluntariado. Ley 5/2004, de 22 de octubre, del Voluntariado en la Región de Murcia.",
    "Tema 34. Competencias de la Comunidad Autónoma de la Región de Murcia en materia de servicios sociales. Ley de Servicios Sociales de la Región de Murcia.",
    "Tema 35. La Consejería de Sanidad y Política Social: estructura y competencias. Ley de creación del IMAS: competencias, funciones y estructura. Los servicios sociales en la Administración del Estado. Los servicios sociales en la Administración Local.",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

@st.cache_resource
def get_client() -> genai.Client:
    """Cliente Gemini instanciado una sola vez por sesión del servidor."""
    api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error(
            "Falta la clave GOOGLE_API_KEY en `secrets.toml`. "
            "Genera una gratis en https://aistudio.google.com/apikey "
            "y pégala en `.streamlit/secrets.toml`."
        )
        st.stop()
    return genai.Client(api_key=api_key)


@st.cache_data
def cargar_examen() -> dict:
    """Carga el JSON del examen 2021 (preguntas + plantilla oficial)."""
    if not EXAMEN_JSON.exists():
        return {"metadata": {}, "preguntas": {}, "respuestas_oficiales": {}}
    with EXAMEN_JSON.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def init_state() -> None:
    """Inicializa una sola vez todas las claves de session_state."""
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("modo", "📚 Desarrollar Temario")
    st.session_state.setdefault("system_prompt", "")


def reset_chat() -> None:
    st.session_state["messages"] = []
    st.session_state["system_prompt"] = ""


def render_history() -> None:
    """Pinta el historial de mensajes con st.chat_message."""
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _to_gemini_contents(messages: list[dict]) -> list[genai_types.Content]:
    """Convierte el historial de Streamlit al formato de Gemini."""
    contents: list[genai_types.Content] = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            genai_types.Content(
                role=role,
                parts=[genai_types.Part.from_text(text=msg["content"])],
            )
        )
    return contents


def stream_assistant_response(system_prompt: str) -> str:
    """
    Llama a la API de Gemini con streaming usando los mensajes acumulados.
    Devuelve el texto completo de la respuesta para guardarlo en el historial.
    """
    client = get_client()
    placeholder = st.empty()
    full_text = ""
    try:
        stream = client.models.generate_content_stream(
            model=MODEL_ID,
            contents=_to_gemini_contents(st.session_state["messages"]),
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=MAX_TOKENS,
                temperature=0.7,
            ),
        )
        for chunk in stream:
            if chunk.text:
                full_text += chunk.text
                placeholder.markdown(full_text + "▌")
        placeholder.markdown(full_text)
    except Exception as exc:  # noqa: BLE001 - mostrar cualquier error al usuario final
        placeholder.error(f"Error al llamar a la API de Gemini: {exc}")
        full_text = f"⚠️ Error: {exc}"
    return full_text


def ask_and_render(user_message: str, system_prompt: str) -> None:
    """
    Añade un mensaje de usuario, dispara una respuesta del asistente y la
    almacena. Se usa tanto desde botones como desde st.chat_input.
    """
    st.session_state["system_prompt"] = system_prompt
    st.session_state["messages"].append({"role": "user", "content": user_message})

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        respuesta = stream_assistant_response(system_prompt)

    st.session_state["messages"].append({"role": "assistant", "content": respuesta})


# ---------------------------------------------------------------------------
# Prompts (system messages)
# ---------------------------------------------------------------------------

SYSTEM_TEMARIO = """Eres un PREPARADOR EXPERTO de oposiciones al Cuerpo de Técnicos Especialistas, opción TERAPEUTA, de la Comunidad Autónoma de la Región de Murcia (CARM). Llevas más de 20 años preparando a alumnos para el Servicio Murciano de Salud y el IMAS.

TU MISIÓN:
Desarrollar de forma EXTENSA, RIGUROSA y ESTRUCTURADA el tema que te pida la alumna. NO HACES RESÚMENES: redactas un auténtico manual de academia, con texto desarrollado, con todos los artículos, definiciones y matices que se preguntan en el examen real.

ESTILO:
- Tono académico pero claro y cercano (la alumna es adulta y está estudiando en casa).
- Estructura con epígrafes numerados (1, 1.1, 1.1.1...) y negritas en los conceptos clave.
- Cita los artículos concretos de cada norma cuando proceda.
- Incluye ejemplos prácticos del día a día de un Terapeuta en residencias, centros de día y centros del IMAS.

⚠️ ACTUALIZACIÓN OBLIGATORIA A 2026 ⚠️
Los temarios oficiales fueron publicados en el BORM en 2014 y 2016 y están DESFASADOS. ESTÁS OBLIGADO a actualizar de oficio toda la legislación a la normativa vigente en el año 2026, advirtiendo a la alumna de los cambios:
- Sustituye Ley 30/1992 por Ley 39/2015 (procedimiento) y Ley 40/2015 (régimen jurídico).
- Sustituye el TRLCSP por la Ley 9/2017 de Contratos del Sector Público y sus modificaciones posteriores.
- Sustituye el RDL 1/2013 por la normativa vigente en discapacidad y dependencia (incluido el Real Decreto 675/2023 sobre nivel mínimo de la dependencia y modificaciones de la Ley 39/2006).
- Actualiza referencias a la LOPD 15/1999 al RGPD 2016/679 y la LOPDGDD 3/2018.
- Incorpora reformas vigentes a 2026 en TREBEP, Ley General de Sanidad, Ley 33/2011 General de Salud Pública, Ley de Servicios Sociales de la Región de Murcia y normativa del IMAS.
- Si una norma citada en el temario original ha sido derogada, dilo expresamente: «La norma X del temario original está derogada; la vigente a 2026 es Y».

CIERRE OBLIGATORIO DE CADA TEMA:
Al final del desarrollo, incluye SIEMPRE dos bloques claramente diferenciados:

## 🔑 5 PUNTOS CLAVE PARA MEMORIZAR
1. ...
2. ...
3. ...
4. ...
5. ...

## 📝 MINI-TEST (3 preguntas)
**1.** Enunciado...
   - A) ...
   - B) ...
   - C) ...
   - D) ...
   *Solución: X — justificación citando el artículo/normativa.*

(misma estructura para las preguntas 2 y 3)
"""

SYSTEM_EXAMEN = """Eres un PREPARADOR EXPERTO de oposiciones al Cuerpo de Técnicos Especialistas, opción TERAPEUTA, de la CARM. Estás corrigiendo con la alumna el examen real celebrado el 23 de octubre de 2021.

Cuando recibas una pregunta, tu cometido es:

1. **CONFIRMAR LA RESPUESTA OFICIAL** según la plantilla del tribunal que te indique el usuario.
2. **EXPLICAR DE FORMA DIDÁCTICA Y MINUCIOSA** por qué esa opción es la ÚNICA correcta. Cita expresamente:
   - El artículo concreto de la ley, real decreto u orden que la sustenta.
   - O la base científica/terapéutica/anatómica/psicopedagógica aplicable.
3. **DESMENUZAR LAS OTRAS TRES OPCIONES** una por una, explicando por qué son incorrectas o por qué son trampas típicas del examen (cambios sutiles de cifras, confusión de leyes derogadas, etc.).
4. Si la legislación citada en la pregunta original (de 2021) ha cambiado en 2026, advierte del cambio pero respeta la respuesta oficial que dio el tribunal en su día.
5. Termina con una **REGLA MNEMOTÉCNICA o pista** para no fallar este tipo de pregunta en el futuro.

Estilo claro, con epígrafes y negritas. Sin rodeos: la alumna quiere entender, no leer paja.
"""


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    with st.sidebar:
        st.title("🎓 Tutor Oposiciones")
        st.caption("Técnico Especialista · Opción Terapeuta · CARM")

        modo = st.radio(
            "Modo de estudio",
            options=["📚 Desarrollar Temario", "📝 Explicar Examen Real (2021)"],
            key="modo",
        )

        st.divider()
        if st.button("🧹 Limpiar Conversación", use_container_width=True, type="primary"):
            reset_chat()
            st.rerun()

        st.divider()
        with st.expander("ℹ️ Sobre esta app"):
            st.markdown(
                "- Modelo: **gemini-2.5-flash** (API gratuita de Google)\n"
                "- La legislación se actualiza automáticamente a **2026**.\n"
                "- Puedes seguir preguntando libremente en el chat de abajo."
            )
    return modo


# ---------------------------------------------------------------------------
# Vista: Desarrollar Temario
# ---------------------------------------------------------------------------

def vista_temario() -> None:
    st.header("📚 Desarrollo de temario")

    col1, col2 = st.columns([1, 2])
    with col1:
        bloque = st.selectbox(
            "Bloque",
            ["Materias Comunes (Anexo III - BORM 2016)",
             "Materias Específicas (Opción Terapeuta - BORM 2014)"],
            key="bloque_temario",
        )

    temas = TEMAS_COMUNES if bloque.startswith("Materias Comunes") else TEMAS_ESPECIFICOS
    with col2:
        tema = st.selectbox("Selecciona el tema a desarrollar", temas, key="tema_seleccionado")

    if st.button("📖 Generar este tema para estudiar", type="primary"):
        user_msg = (
            f"Desarróllame por favor el siguiente tema del bloque «{bloque}» como "
            f"un manual completo de academia, actualizado a 2026:\n\n**{tema}**"
        )
        ask_and_render(user_msg, SYSTEM_TEMARIO)


# ---------------------------------------------------------------------------
# Vista: Examen Real 2021
# ---------------------------------------------------------------------------

def formato_pregunta(num: int, data: dict) -> Optional[str]:
    """Devuelve el bloque markdown con la pregunta, o None si no hay datos."""
    pregunta = data.get("preguntas", {}).get(str(num))
    if not pregunta:
        return None
    opciones = pregunta.get("opciones", {})
    bloque = [f"**Pregunta {num}.** {pregunta.get('enunciado', '')}", ""]
    for letra in ("A", "B", "C", "D"):
        if letra in opciones:
            bloque.append(f"- **{letra})** {opciones[letra]}")
    return "\n".join(bloque)


def vista_examen() -> None:
    st.header("📝 Examen real - 23 de octubre de 2021")
    data = cargar_examen()

    num = st.number_input(
        "Número de pregunta (1 a 100)",
        min_value=1, max_value=100, value=1, step=1,
        key="num_pregunta",
    )

    plantilla = data.get("respuestas_oficiales", {}).get(str(num))
    bloque_pregunta = formato_pregunta(num, data)

    with st.container(border=True):
        if bloque_pregunta:
            st.markdown(bloque_pregunta)
        else:
            st.warning(
                f"La pregunta {num} aún no tiene su enunciado cargado en "
                "`examen_data.json`. Puedes añadirla manualmente o pedir igualmente "
                "la explicación: el tutor trabajará a partir de la respuesta oficial."
            )
        if plantilla:
            st.success(f"✅ Respuesta oficial del tribunal: **{plantilla}**")
        else:
            st.info("Respuesta oficial no registrada en la plantilla local.")

    if st.button("💡 Solicitar explicación detallada de la pregunta", type="primary"):
        if bloque_pregunta:
            user_msg = (
                f"Explícame la pregunta {num} del examen del 23/10/2021.\n\n"
                f"{bloque_pregunta}\n\n"
                f"Respuesta oficial del tribunal: **{plantilla or 'no disponible en plantilla local'}**.\n\n"
                "Justifica por qué es correcta y por qué las otras tres opciones no lo son."
            )
        else:
            user_msg = (
                f"Explícame la pregunta {num} del examen del 23/10/2021 del Cuerpo de "
                f"Técnicos Especialistas opción Terapeuta de la CARM. "
                f"La respuesta oficial del tribunal fue: "
                f"**{plantilla or 'desconocida'}**. "
                "No tengo cargado el enunciado literal: explícame qué se preguntaba "
                "habitualmente en esa posición del examen según el temario oficial "
                "y por qué esa letra es la correcta."
            )
        ask_and_render(user_msg, SYSTEM_EXAMEN)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    init_state()
    modo = render_sidebar()

    if modo == "📚 Desarrollar Temario":
        vista_temario()
        system_activo = SYSTEM_TEMARIO
    else:
        vista_examen()
        system_activo = SYSTEM_EXAMEN

    st.divider()
    st.subheader("💬 Conversación con el tutor")
    render_history()

    prompt_usuario = st.chat_input("Pregunta lo que quieras al tutor (aclaraciones, ejemplos, mnemotecnias...)")
    if prompt_usuario:
        # Usamos el system prompt activo según el modo actual (o el último usado).
        system_prompt = st.session_state.get("system_prompt") or system_activo
        ask_and_render(prompt_usuario, system_prompt)


if __name__ == "__main__":
    main()
