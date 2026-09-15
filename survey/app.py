"""
FoodMedKG human evaluation survey — Streamlit app.

A rotating-block survey: each respondent only rates the items assigned to
the block named in the URL (?block=...). Responses are appended to a
Google Sheet (worksheet "responses") via a service account, so nothing is
persisted to local disk — required for Streamlit Community Cloud, whose
filesystem is ephemeral and not shared across sessions/instances.
"""

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------------
# Placeholders — fill these in before real deployment.
# --------------------------------------------------------------------------

CONSENT_TEXT = (
    "Te invitamos a participar en un estudio de investigación que evalúa "
    "**FoodMedKG**, un grafo de conocimiento que relaciona alimentos con "
    "enfermedades, indicadores de envejecimiento y métodos de cocción, "
    "desarrollado como parte de un proyecto de investigación de la "
    "**Universidad de Granada**. Se te pedirá que revises un pequeño "
    "conjunto de relaciones alimento-salud extraídas del grafo de "
    "conocimiento y que valores si cada una es correcta y si está "
    "simplificada en exceso. La encuesta tarda entre 10 y 12 minutos en "
    "completarse.\n\n"
    "La participación es totalmente **voluntaria y anónima**: no "
    "recogemos tu nombre, correo electrónico ni ninguna otra información "
    "identificativa. La única información que se solicita sobre ti (año "
    "de curso, especialidad, género, edad y nivel de inglés) se usa "
    "únicamente para describir al grupo de participantes de forma "
    "agregada. Puedes dejar de participar en cualquier momento antes de "
    "enviar el formulario sin ninguna consecuencia; una vez enviado, las "
    "respuestas individuales no se pueden retirar, ya que no están "
    "vinculadas a tu identidad.\n\n"
    "Tus respuestas se utilizarán únicamente de forma agregada, con "
    "fines de investigación académica, y no se compartirán de forma "
    "individual. Si tienes cualquier pregunta sobre este estudio, puedes "
    "contactar con Andrea Morales Garzón en amoralesg@ugr.es.\n\n"
    "Al marcar la casilla de abajo, confirmas que has leído esta "
    "información y que aceptas participar de forma voluntaria."
)

# Name of the Google Sheet (spreadsheet) that stores responses.
# TODO: replace with the real spreadsheet name/ID once it is created.
SPREADSHEET_NAME = "FoodMedKG_Survey_Responses"  # placeholder
RESPONSES_WORKSHEET = "responses"

# Resolved relative to this file, not the working directory: Streamlit
# Community Cloud runs the app with the repo root as cwd (even though the
# main file lives at survey/app.py), so a bare "items.csv" would 404 there
# despite working locally when launched via `cd survey && streamlit run`.
ITEMS_CSV_PATH = Path(__file__).parent / "items.csv"

YEAR_OF_STUDY_OPTIONS = ["1", "2", "3", "4", "5", "6", "Postgrado"]
SPECIALIZATION_OPTIONS = ["Nutrición", "Dietética", "Otra"]
GENDER_OPTIONS = ["Mujer", "Hombre", "No binario", "Prefiero no decirlo", "Otro"]
ENGLISH_LEVEL_OPTIONS = [
    "Principiante (A1-A2)",
    "Intermedio (B1-B2)",
    "Avanzado (C1-C2)",
    "Nativo / bilingüe",
]
CORRECTNESS_OPTIONS = ["De acuerdo", "En desacuerdo", "No estoy seguro/a"]
OVERSIMPLIFIED_OPTIONS = ["Sí", "No"]

MIN_AGE = 16
MAX_AGE = 100

RESPONSE_COLUMNS = [
    "timestamp",
    "respondent_id",
    "block_id",
    "year_of_study",
    "specialization",
    "gender",
    "age",
    "english_level",
    "item_id",
    "type",
    "food",
    "target",
    "correctness",
    "oversimplified",
    "comment",
]

st.set_page_config(page_title="Encuesta de Evaluación FoodMedKG", layout="centered")


# --------------------------------------------------------------------------
# Block routing via URL query parameter.
#
# Block assignment is deliberately NOT randomized or guessed here: study
# coordinators hand out distinct links (e.g. .../?block=3) to different
# sub-groups of students so each respondent only ever sees their assigned
# subset of items. If the query param is absent/invalid we refuse to guess
# and show a landing screen instead.
# --------------------------------------------------------------------------
def get_requested_block() -> str | None:
    query_params = st.query_params
    block = query_params.get("block")
    if block is None or block == "":
        return None
    return str(block)


@st.cache_data
def load_items(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df["block_id"] = df["block_id"].astype(str)
    return df


def get_block_items(items_df: pd.DataFrame, block_id: str) -> pd.DataFrame:
    return items_df[items_df["block_id"] == block_id].reset_index(drop=True)


# --------------------------------------------------------------------------
# Google Sheets persistence.
#
# Credentials come from st.secrets["gcp_service_account"], which mirrors the
# standard Streamlit + gspread deployment pattern: a service account JSON
# key is pasted into .streamlit/secrets.toml (locally) or the Streamlit
# Community Cloud "Secrets" panel (in production), and the target Sheet is
# shared with that service account's client_email as an Editor.
# --------------------------------------------------------------------------
@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(credentials)


def get_responses_worksheet():
    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        return spreadsheet.worksheet(RESPONSES_WORKSHEET)
    except gspread.exceptions.WorksheetNotFound:
        pass

    # Two respondents submitting at almost the same instant could both reach
    # here before either has created the worksheet. Only one add_worksheet
    # call can actually win (Sheets rejects a duplicate title); treat that
    # as success and just fetch the worksheet the other request created.
    try:
        worksheet = spreadsheet.add_worksheet(
            title=RESPONSES_WORKSHEET, rows=1000, cols=len(RESPONSE_COLUMNS)
        )
        worksheet.append_row(RESPONSE_COLUMNS)
        return worksheet
    except gspread.exceptions.APIError:
        return spreadsheet.worksheet(RESPONSES_WORKSHEET)


def append_responses(rows: list[list[str]]) -> None:
    """Append all of a respondent's rows in a single API call.

    Batching keeps well under Google Sheets' per-minute write quota (60
    write requests/minute for a single service account), which is easy to
    trip if every item were appended individually (e.g. 20 items x 40
    students = 800 calls vs. 40 calls) — this matters here because blocks
    are rotated across ~40 students who may well submit within the same
    few-minute window.

    A short retry with backoff is added on top in case several submissions
    still land in the same second and briefly trip the quota regardless.
    """
    # Retried on 429 (quota) and transient 5xx errors from Google's side;
    # anything else (e.g. bad credentials, permission errors) is raised
    # immediately since retrying it would never succeed.
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    worksheet = get_responses_worksheet()
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            worksheet.append_rows(rows, value_input_option="USER_ENTERED")
            return
        except gspread.exceptions.APIError as exc:
            if exc.code not in RETRYABLE_CODES or attempt == max_attempts - 1:
                raise
            time.sleep(2**attempt)  # 1s, 2s, 4s backoff before retrying


# --------------------------------------------------------------------------
# Session state setup.
# --------------------------------------------------------------------------
if "respondent_id" not in st.session_state:
    # One anonymous UUID per browser session, shared by every row this
    # respondent submits. No name/email is ever collected.
    st.session_state.respondent_id = str(uuid.uuid4())

if "submitted" not in st.session_state:
    st.session_state.submitted = False


# --------------------------------------------------------------------------
# Landing screen — shown when no valid block is present in the URL.
# --------------------------------------------------------------------------
def render_landing_screen():
    st.title("Encuesta de Evaluación FoodMedKG")
    st.warning(
        "No se ha encontrado un bloque de encuesta válido en este "
        "enlace.\n\n"
        "Por favor, utiliza exactamente el enlace que te han compartido "
        "los coordinadores del estudio (debería tener un aspecto como "
        "`...?block=3`). Si crees que se trata de un error, contacta con "
        "el equipo de investigación en lugar de probar un número de "
        "bloque al azar."
    )


def render_thank_you():
    st.title("¡Gracias!")
    st.success(
        "Tus respuestas se han guardado correctamente. Ya puedes cerrar "
        "esta pestaña. Gracias por contribuir al estudio de evaluación "
        "de FoodMedKG."
    )


# --------------------------------------------------------------------------
# Main survey rendering.
# --------------------------------------------------------------------------
def render_survey(block_id: str, block_items: pd.DataFrame):
    st.title("Encuesta de Evaluación FoodMedKG")
    st.caption(f"Bloque {block_id} — {len(block_items)} ítems")

    with st.form("survey_form", clear_on_submit=False):
        # --- Consent + demographic header (shown once, above the items) ---
        st.subheader("Antes de empezar")
        st.markdown(CONSENT_TEXT)
        consent_given = st.checkbox(
            "He leído la información anterior y acepto participar en este estudio."
        )

        col1, col2 = st.columns(2)
        with col1:
            year_of_study = st.selectbox(
                "Año de curso",
                YEAR_OF_STUDY_OPTIONS,
                index=None,
                placeholder="Selecciona tu año de curso",
            )
        with col2:
            specialization = st.selectbox(
                "Especialidad / área",
                SPECIALIZATION_OPTIONS,
                index=None,
                placeholder="Selecciona tu especialidad",
            )

        col3, col4, col5 = st.columns(3)
        with col3:
            gender = st.selectbox(
                "Género",
                GENDER_OPTIONS,
                index=None,
                placeholder="Selecciona tu género",
            )
        with col4:
            # min_value is set below the real minimum (0) so the field
            # starts at an obviously-unset sentinel rather than at
            # value=None, which disables the +/- stepper buttons in
            # Streamlit until the user types a number manually.
            age = st.number_input(
                "Edad",
                min_value=0,
                max_value=MAX_AGE,
                value=0,
                step=1,
                help=f"Usa +/- o escribe tu edad (debe ser de al menos {MIN_AGE} años).",
            )
        with col5:
            english_level = st.selectbox(
                "Nivel de inglés",
                ENGLISH_LEVEL_OPTIONS,
                index=None,
                placeholder="Selecciona tu nivel",
            )

        st.divider()
        st.subheader("Ítems a evaluar")
        st.caption(
            "Cada ítem incluye una cita de referencia: puedes consultarla si "
            "quieres comprobar la evidencia antes de responder, pero no es "
            "obligatorio hacerlo."
        )

        # --- One rating block per item ---
        # index=None keeps radios unselected by default so we can detect
        # and reject incomplete submissions instead of silently recording
        # a false default answer.
        answers = {}
        for i, row in block_items.iterrows():
            st.markdown(f"**Ítem {i + 1} de {len(block_items)}**")
            if row.get("relation_text"):
                st.markdown(row["relation_text"])
            if row.get("relation_text_es"):
                st.info(f"**Traducción:** {row['relation_text_es']}")
            if pd.notna(row.get("link")) and str(row.get("link")).strip():
                st.markdown(f"[Cita de referencia]({row['link']}) — {row.get('citation', '')}")
            elif row.get("citation"):
                st.caption(f"Cita: {row['citation']}")

            correctness = st.radio(
                "¿Es correcta esta relación?",
                CORRECTNESS_OPTIONS,
                index=None,
                key=f"correctness_{row['item_id']}",
                horizontal=True,
            )
            oversimplified = st.radio(
                "¿Es una simplificación excesiva?",
                OVERSIMPLIFIED_OPTIONS,
                index=None,
                key=f"oversimplified_{row['item_id']}",
                horizontal=True,
            )
            comment = st.text_area(
                "Comentario (opcional)",
                key=f"comment_{row['item_id']}",
                height=68,
            )
            answers[row["item_id"]] = {
                "row": row,
                "correctness": correctness,
                "oversimplified": oversimplified,
                "comment": comment,
            }
            st.divider()

        submitted = st.form_submit_button("Enviar", use_container_width=True)

    if not submitted:
        return

    # --- Validation ---
    errors = []
    if not consent_given:
        errors.append("Debes aceptar el consentimiento anterior para participar.")
    if not year_of_study:
        errors.append("El año de curso es obligatorio.")
    if not specialization:
        errors.append("La especialidad es obligatoria.")
    if not gender:
        errors.append("El género es obligatorio.")
    if age < MIN_AGE:
        errors.append(f"La edad es obligatoria y debe ser de al menos {MIN_AGE} años.")
    if not english_level:
        errors.append("El nivel de inglés es obligatorio.")

    incomplete_items = [
        item_id
        for item_id, a in answers.items()
        if a["correctness"] is None or a["oversimplified"] is None
    ]
    if incomplete_items:
        errors.append(
            "Los siguientes ítems tienen alguna respuesta obligatoria sin "
            "rellenar: " + ", ".join(incomplete_items)
        )

    if errors:
        for e in errors:
            st.error(e)
        return

    # --- Build rows and submit as a single batched append ---
    timestamp = datetime.now(timezone.utc).isoformat()
    rows = []
    for item_id, a in answers.items():
        row = a["row"]
        rows.append(
            [
                timestamp,
                st.session_state.respondent_id,
                block_id,
                year_of_study,
                specialization,
                gender,
                int(age),
                english_level,
                item_id,
                row["type"],
                row["food"],
                row["target"],
                a["correctness"],
                a["oversimplified"],
                a["comment"] or "",
            ]
        )

    try:
        append_responses(rows)
    except Exception as exc:  # noqa: BLE001 - surface any Sheets/auth error to the user
        st.error(
            "Ha habido un problema al guardar tus respuestas. Por favor, "
            "no cierres esta pestaña — contacta con el equipo del estudio "
            f"indicando este error: {exc}"
        )
        return

    st.session_state.submitted = True
    st.rerun()


# --------------------------------------------------------------------------
# Entry point.
# --------------------------------------------------------------------------
def main():
    if st.session_state.submitted:
        render_thank_you()
        return

    block_id = get_requested_block()
    if block_id is None:
        render_landing_screen()
        return

    items_df = load_items(ITEMS_CSV_PATH)
    block_items = get_block_items(items_df, block_id)

    if block_items.empty:
        render_landing_screen()
        return

    render_survey(block_id, block_items)


if __name__ == "__main__":
    main()
