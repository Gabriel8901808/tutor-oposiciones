"""
Tutor Interactivo de Oposiciones - Técnico Especialista (Opción Terapeuta) - CARM.

Aplicación Streamlit que usa la API gratuita de Google Gemini como preparador
personal. Tres modos: desarrollar temario, hacer tests autoevaluables (con
niveles y combinando temas) y explicar el examen real de 2021.

Los temarios se cargan desde `temarios.json`, de modo que se pueden añadir
nuevos temarios sin tocar el código.
"""

from __future__ import annotations

import json
import re
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
BASE_DIR = Path(__file__).parent
EXAMEN_JSON = BASE_DIR / "examen_data.json"
TEMARIOS_JSON = BASE_DIR / "temarios.json"

NIVELES = {
    "Fácil": "preguntas directas sobre definiciones y conceptos básicos del tema.",
    "Medio": "preguntas de aplicación, con matices y citando artículos o datos concretos.",
    "Difícil": "preguntas tipo examen real: casos prácticos, trampas sutiles, cifras y plazos exactos, y distinción fina entre opciones muy parecidas.",
    "Mixto": "una mezcla equilibrada de preguntas fáciles, medias y difíciles.",
}

MODOS = [
    "📚 Desarrollar Temario",
    "🧪 Hacer Test",
    "📝 Explicar Examen Real (2021)",
]


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

@st.cache_data
def cargar_temarios() -> dict:
    """Devuelve {nombre_temario: {'etiqueta', 'fuente', 'temas': [...]}}."""
    if not TEMARIOS_JSON.exists():
        return {}
    with TEMARIOS_JSON.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("temarios", {})


@st.cache_data
def cargar_examen() -> dict:
    """Carga el JSON del examen 2021 (preguntas + plantilla oficial)."""
    if not EXAMEN_JSON.exists():
        return {"metadata": {}, "preguntas": {}, "respuestas_oficiales": {}}
    with EXAMEN_JSON.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def titulo_corto(tema: str, limite: int = 70) -> str:
    """'Tema 7. La discapacidad intelectual. Concepto...' -> versión corta."""
    tema = tema.strip()
    # Cortamos en el primer punto tras 'Tema N.'
    m = re.match(r"(Tema\s+\d+\.\s+[^.]+\.)", tema)
    base = m.group(1) if m else tema
    if len(base) > limite:
        base = base[: limite - 1].rstrip() + "…"
    return base


# ---------------------------------------------------------------------------
# Cliente Gemini
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


def _to_gemini_contents(messages: list[dict]) -> list[genai_types.Content]:
    contents: list[genai_types.Content] = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            genai_types.Content(role=role, parts=[genai_types.Part.from_text(text=msg["content"])])
        )
    return contents


def stream_assistant_response(system_prompt: str) -> str:
    """Llama a Gemini con streaming usando el historial; devuelve el texto."""
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
    except Exception as exc:  # noqa: BLE001
        placeholder.error(f"Error al llamar a la API de Gemini: {exc}")
        full_text = f"⚠️ Error: {exc}"
    return full_text


def generar_json(system_prompt: str, user_prompt: str) -> dict:
    """Llamada NO streaming que devuelve JSON (para generar tests)."""
    client = get_client()
    resp = client.models.generate_content(
        model=MODEL_ID,
        contents=user_prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_TOKENS,
            temperature=0.9,
            response_mime_type="application/json",
        ),
    )
    texto = resp.text or "{}"
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        # Rescate: extraer el primer objeto { ... } del texto
        m = re.search(r"\{.*\}", texto, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("system_prompt", "")
    st.session_state.setdefault("test", None)          # dict con preguntas
    st.session_state.setdefault("test_corregido", False)


def reset_chat() -> None:
    st.session_state["messages"] = []
    st.session_state["system_prompt"] = ""


def render_history() -> None:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def ask_and_render(user_message: str, system_prompt: str) -> None:
    """Añade un mensaje del usuario y muestra la respuesta del tutor."""
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

CONTEXTO_BASE = (
    "Eres un PREPARADOR EXPERTO de oposiciones al Cuerpo de Técnicos Especialistas, "
    "opción TERAPEUTA, de la Comunidad Autónoma de la Región de Murcia (CARM). "
    "Llevas más de 20 años preparando alumnos para el Servicio Murciano de Salud y el IMAS. "
    "Conoces a fondo los manuales de los ciclos de Grado Superior de Integración Social, "
    "Animación Sociocultural y Terapia Ocupacional, además de la normativa estatal y autonómica."
)

ACTUALIZACION_2026 = """⚠️ ACTUALIZACIÓN OBLIGATORIA A 2026 ⚠️
Los temarios oficiales son de 2014 y 2016 y están DESFASADOS. Actualiza SIEMPRE la legislación a la vigente en 2026 y avisa de los cambios:
- Ley 30/1992 → Ley 39/2015 (procedimiento) y Ley 40/2015 (régimen jurídico).
- TRLCSP → Ley 9/2017 de Contratos del Sector Público.
- RDL 1/2013 y normativa de dependencia → marco vigente 2026 (incluido el Real Decreto 675/2023 y reformas de la Ley 39/2006).
- LOPD 15/1999 → RGPD 2016/679 y LOPDGDD 3/2018.
- Si una norma del temario original está derogada, dilo: «La norma X está derogada; la vigente a 2026 es Y»."""

SYSTEM_TEMARIO = f"""{CONTEXTO_BASE}

TU MISIÓN: desarrollar de forma EXTENSA, RIGUROSA y ESTRUCTURADA el tema que te pidan. NO HACES RESÚMENES: redactas un auténtico manual de academia, con texto desarrollado, artículos, definiciones y matices que se preguntan en el examen real. Para los temas específicos, apóyate en el contenido de los manuales de FP de Grado Superior de Integración Social, Animación Sociocultural y Terapia Ocupacional.

ESTILO:
- Tono académico pero claro y cercano (la alumna es adulta y estudia en casa).
- Epígrafes numerados (1, 1.1, 1.1.1...) y negritas en los conceptos clave.
- Cita los artículos concretos de cada norma cuando proceda.
- Incluye ejemplos prácticos del día a día de un Terapeuta en residencias, centros de día y centros del IMAS.

{ACTUALIZACION_2026}

CIERRE OBLIGATORIO DE CADA TEMA, con estos dos bloques:

## 🔑 5 PUNTOS CLAVE PARA MEMORIZAR
(5 puntos numerados)

## 📝 MINI-TEST (3 preguntas)
(3 preguntas con opciones A-D y su solución justificada citando el artículo o la base científica)
"""

SYSTEM_EXAMEN = f"""{CONTEXTO_BASE}

Estás corrigiendo con la alumna el examen real del 23 de octubre de 2021. Cuando recibas una pregunta:

1. CONFIRMA la respuesta oficial de la plantilla del tribunal.
2. EXPLICA de forma didáctica y minuciosa por qué esa opción es la ÚNICA correcta, citando el artículo concreto de la ley/real decreto/orden o la base científica/terapéutica aplicable.
3. DESMENUZA las otras tres opciones, explicando por qué son incorrectas o por qué son trampas típicas del examen.
4. Si la legislación de 2021 ha cambiado en 2026, avísalo pero respeta la respuesta oficial que dio el tribunal.
5. Termina con una REGLA MNEMOTÉCNICA o pista para no fallar este tipo de pregunta.

Estilo claro, con epígrafes y negritas. Sin rodeos."""

SYSTEM_TEST = f"""{CONTEXTO_BASE}

Generas TESTS de opción múltiple (estilo examen oficial de la CARM) sobre los temas que te indiquen. {ACTUALIZACION_2026}

REGLAS:
- Cada pregunta tiene EXACTAMENTE 4 opciones (A, B, C, D) y SOLO UNA correcta.
- Las opciones incorrectas deben ser plausibles (trampas realistas: cifras cambiadas, leyes derogadas, conceptos parecidos).
- Varía el tema de origen si te dan varios.
- La justificación debe citar el artículo de la norma vigente a 2026 o la base científica/terapéutica.

Devuelve EXCLUSIVAMENTE un JSON válido con esta forma EXACTA:
{{
  "preguntas": [
    {{
      "enunciado": "texto de la pregunta",
      "opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correcta": "A",
      "justificacion": "por qué es correcta (citando norma 2026 o base científica) y, brevemente, por qué fallan las demás"
    }}
  ]
}}
No añadas texto fuera del JSON."""

SYSTEM_TUTOR_GENERAL = (
    CONTEXTO_BASE
    + " Resuelve con claridad las dudas de la alumna, con ejemplos y reglas para memorizar. "
    + ACTUALIZACION_2026
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    with st.sidebar:
        st.title("🎓 Tutor Oposiciones")
        st.caption("Técnico Especialista · Opción Terapeuta · CARM")

        modo = st.radio("¿Qué quieres hacer?", options=MODOS, key="modo")

        st.divider()
        if st.button("🧹 Limpiar Conversación", use_container_width=True, type="primary"):
            reset_chat()
            st.rerun()

        st.divider()
        with st.expander("ℹ️ Sobre esta app"):
            st.markdown(
                "- Modelo: **gemini-2.5-flash** (API gratuita de Google).\n"
                "- La legislación se actualiza automáticamente a **2026**.\n"
                "- En *Hacer Test* puedes combinar temas y elegir el nivel.\n"
                "- Para añadir nuevos temarios, edita `temarios.json`."
            )
    return modo


# ---------------------------------------------------------------------------
# Vista: Desarrollar Temario
# ---------------------------------------------------------------------------

def vista_temario(temarios: dict) -> None:
    st.header("📚 Desarrollo de temario")
    if not temarios:
        st.error("No se ha podido cargar `temarios.json`.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        nombre = st.selectbox("Bloque / Temario", list(temarios.keys()), key="bloque_temario")
    temas = temarios[nombre]["temas"]
    with col2:
        tema = st.selectbox("Selecciona el tema a desarrollar", temas, key="tema_seleccionado")

    if st.button("📖 Generar este tema para estudiar", type="primary"):
        user_msg = (
            f"Desarróllame como un manual completo de academia, actualizado a 2026, "
            f"el siguiente tema del bloque «{nombre}»:\n\n**{tema}**"
        )
        ask_and_render(user_msg, SYSTEM_TEMARIO)


# ---------------------------------------------------------------------------
# Vista: Hacer Test
# ---------------------------------------------------------------------------

def vista_test(temarios: dict) -> None:
    st.header("🧪 Generador de tests")
    st.caption("Elige uno o varios temas (puedes combinarlos), el nivel y cuántas preguntas quieres.")

    # Construir el catálogo combinado de temas de TODOS los temarios
    catalogo: dict[str, dict] = {}
    for nombre, info in temarios.items():
        etiqueta = info.get("etiqueta", nombre)
        for tema in info["temas"]:
            label = f"[{etiqueta}] {titulo_corto(tema)}"
            catalogo[label] = {"temario": nombre, "tema": tema}

    seleccion = st.multiselect(
        "Temas a incluir en el test",
        options=list(catalogo.keys()),
        key="test_temas",
        help="Puedes mezclar temas de Materias Comunes y Específicas.",
    )

    c1, c2 = st.columns(2)
    with c1:
        nivel = st.select_slider("Nivel de dificultad", options=list(NIVELES.keys()), value="Medio", key="test_nivel")
    with c2:
        num = st.slider("Número de preguntas", min_value=3, max_value=20, value=5, key="test_num")

    cgen, cclear = st.columns([3, 1])
    with cgen:
        generar = st.button("🎲 Generar test", type="primary", use_container_width=True)
    with cclear:
        if st.button("🗑️ Borrar", use_container_width=True):
            st.session_state["test"] = None
            st.session_state["test_corregido"] = False
            st.rerun()

    if generar:
        if not seleccion:
            st.warning("Selecciona al menos un tema para generar el test.")
        else:
            temas_txt = "\n".join(f"- {catalogo[s]['tema']} (Bloque: {catalogo[s]['temario']})" for s in seleccion)
            user_prompt = (
                f"Genera un test de {num} preguntas de nivel «{nivel}» "
                f"({NIVELES[nivel]}) sobre los siguientes temas:\n{temas_txt}\n\n"
                "Reparte las preguntas entre los temas indicados. Devuelve solo el JSON."
            )
            with st.spinner("Generando preguntas con el tutor…"):
                try:
                    data = generar_json(SYSTEM_TEST, user_prompt)
                    preguntas = data.get("preguntas", [])
                    # Validación mínima
                    preguntas = [
                        q for q in preguntas
                        if isinstance(q.get("opciones"), dict)
                        and {"A", "B", "C", "D"} <= set(q["opciones"])
                        and q.get("correcta") in {"A", "B", "C", "D"}
                    ]
                    if not preguntas:
                        st.error("No se pudieron generar preguntas válidas. Inténtalo otra vez.")
                    else:
                        st.session_state["test"] = {"preguntas": preguntas, "nivel": nivel}
                        st.session_state["test_corregido"] = False
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error al generar el test: {exc}")

    _render_test_actual()


def _render_test_actual() -> None:
    test = st.session_state.get("test")
    if not test:
        return

    preguntas = test["preguntas"]
    st.divider()
    st.subheader(f"📋 Test ({len(preguntas)} preguntas · nivel {test['nivel']})")

    with st.form("formulario_test"):
        for i, q in enumerate(preguntas):
            st.markdown(f"**{i + 1}. {q['enunciado']}**")
            st.radio(
                "Tu respuesta:",
                options=["A", "B", "C", "D"],
                format_func=lambda L, q=q: f"{L}) {q['opciones'][L]}",
                index=None,
                key=f"resp_{i}",
                label_visibility="collapsed",
            )
            st.write("")
        enviado = st.form_submit_button("✅ Corregir test", type="primary")

    if enviado:
        st.session_state["test_corregido"] = True

    if st.session_state.get("test_corregido"):
        _mostrar_resultados(preguntas)


def _mostrar_resultados(preguntas: list[dict]) -> None:
    aciertos = 0
    sin_responder = 0
    for i, q in enumerate(preguntas):
        if st.session_state.get(f"resp_{i}") == q["correcta"]:
            aciertos += 1
        elif st.session_state.get(f"resp_{i}") is None:
            sin_responder += 1

    total = len(preguntas)
    nota = round(aciertos / total * 10, 2)
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Aciertos", f"{aciertos}/{total}")
    c2.metric("Nota (sobre 10)", nota)
    c3.metric("Sin responder", sin_responder)

    # Mensaje de ánimo (siempre, salga como salga el test)
    st.success(
        "💙 **Mamá, salga como salga este test, NO TE RINDAS.** "
        "Cada pregunta que haces, aciertes o falles, es un paso más cerca de conseguirlo. "
        "Estoy muy orgulloso del esfuerzo enorme que le pones cada día. "
        "Lo estás haciendo genial y vas a poder con esto. "
        "**Tu hijo Gabriel te quiere muchísimo.** 💪❤️"
    )

    st.subheader("📖 Corrección detallada")
    for i, q in enumerate(preguntas):
        elegida = st.session_state.get(f"resp_{i}")
        correcta = q["correcta"]
        if elegida == correcta:
            icono = "✅"
        elif elegida is None:
            icono = "⬜"
        else:
            icono = "❌"
        with st.expander(f"{icono} Pregunta {i + 1}: {q['enunciado'][:80]}…"):
            for L in ("A", "B", "C", "D"):
                marca = ""
                if L == correcta:
                    marca = " ✅ **(correcta)**"
                elif L == elegida:
                    marca = " ❌ (tu respuesta)"
                st.markdown(f"- **{L})** {q['opciones'][L]}{marca}")
            st.info(f"**Justificación:** {q.get('justificacion', '(sin justificación)')}")


# ---------------------------------------------------------------------------
# Vista: Examen Real 2021
# ---------------------------------------------------------------------------

def formato_pregunta(num: int, data: dict) -> Optional[str]:
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
        "Número de pregunta (1 a 100)", min_value=1, max_value=100, value=1, step=1, key="num_pregunta"
    )
    plantilla = data.get("respuestas_oficiales", {}).get(str(num))
    bloque_pregunta = formato_pregunta(num, data)

    with st.container(border=True):
        if bloque_pregunta:
            st.markdown(bloque_pregunta)
        else:
            st.warning(f"La pregunta {num} no está cargada en `examen_data.json`.")
        if plantilla:
            st.success(f"✅ Respuesta oficial del tribunal: **{plantilla}**")
        else:
            st.info("Respuesta oficial no registrada en la plantilla local.")

    if st.button("💡 Solicitar explicación detallada de la pregunta", type="primary"):
        if bloque_pregunta:
            user_msg = (
                f"Explícame la pregunta {num} del examen del 23/10/2021.\n\n{bloque_pregunta}\n\n"
                f"Respuesta oficial del tribunal: **{plantilla or 'no disponible'}**.\n\n"
                "Justifica por qué es correcta y por qué las otras tres opciones no lo son."
            )
        else:
            user_msg = (
                f"Explícame la pregunta {num} del examen del 23/10/2021 del Cuerpo de Técnicos "
                f"Especialistas opción Terapeuta de la CARM. La respuesta oficial fue "
                f"**{plantilla or 'desconocida'}**. Explica el tema sobre el que solía preguntar."
            )
        ask_and_render(user_msg, SYSTEM_EXAMEN)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    init_state()
    temarios = cargar_temarios()
    modo = render_sidebar()

    if modo == "📚 Desarrollar Temario":
        vista_temario(temarios)
        system_activo = SYSTEM_TEMARIO
        mostrar_chat = True
    elif modo == "🧪 Hacer Test":
        vista_test(temarios)
        system_activo = SYSTEM_TUTOR_GENERAL
        mostrar_chat = True
    else:
        vista_examen()
        system_activo = SYSTEM_EXAMEN
        mostrar_chat = True

    if mostrar_chat:
        st.divider()
        st.subheader("💬 Conversación con el tutor")
        st.caption("Pregunta cualquier duda: aclaraciones, otro ejemplo, una regla para memorizar…")
        render_history()
        prompt_usuario = st.chat_input("Escribe aquí tu duda para el tutor…")
        if prompt_usuario:
            system_prompt = st.session_state.get("system_prompt") or system_activo
            ask_and_render(prompt_usuario, system_prompt)


if __name__ == "__main__":
    main()
