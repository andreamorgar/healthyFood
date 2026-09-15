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

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------------
# Placeholders — fill these in before real deployment.
# --------------------------------------------------------------------------

# TODO: replace with the final consent/info paragraph provided by the study
# authors before distributing real block links to students.
CONSENT_TEXT = (
    "You are invited to take part in a research study evaluating "
    "**FoodMedKG**, a knowledge graph linking foods to diseases, aging "
    "indicators, and cooking methods, developed as part of a research "
    "project at the **University of Granada**. You will be asked to "
    "review a small set of food–health relations extracted from the "
    "knowledge graph and judge whether each one is correct and whether "
    "it is oversimplified. The survey takes about 10–12 minutes to "
    "complete.\n\n"
    "Participation is entirely **voluntary and anonymous**: we do not "
    "collect your name, email, or any other identifying information. The "
    "only information requested about you (year of study, specialization, "
    "gender, age, and level of English) is used solely to describe the "
    "group of respondents in aggregate. You may stop at any point before "
    "submitting without consequence; once submitted, individual responses "
    "cannot be withdrawn, since they are not linked to your identity.\n\n"
    "Your responses will be used only in aggregate, for academic research "
    "purposes, and will not be shared individually. If you have any "
    "questions about this study, you can contact Andrea Morales Garzón "
    "at amoralesg@ugr.es.\n\n"
    "By checking the box below, you confirm that you have read this "
    "information and voluntarily agree to participate."
)

# Name of the Google Sheet (spreadsheet) that stores responses.
# TODO: replace with the real spreadsheet name/ID once it is created.
SPREADSHEET_NAME = "FoodMedKG_Survey_Responses"  # placeholder
RESPONSES_WORKSHEET = "responses"

ITEMS_CSV_PATH = "items.csv"

YEAR_OF_STUDY_OPTIONS = ["1", "2", "3", "4", "5", "6", "Postgraduate"]
SPECIALIZATION_OPTIONS = ["Nutrition", "Dietetics", "Medicine", "Other"]
GENDER_OPTIONS = ["Female", "Male", "Non-binary", "Prefer not to say", "Other"]
ENGLISH_LEVEL_OPTIONS = [
    "Beginner (A1-A2)",
    "Intermediate (B1-B2)",
    "Advanced (C1-C2)",
    "Native / bilingual",
]
CORRECTNESS_OPTIONS = ["Agree", "Disagree", "Not sure"]
OVERSIMPLIFIED_OPTIONS = ["Yes", "No"]

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

st.set_page_config(page_title="FoodMedKG Evaluation Survey", layout="centered")


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
    st.title("FoodMedKG Evaluation Survey")
    st.warning(
        "No valid survey block was found in this link.\n\n"
        "Please use the exact link that was shared with you by the study "
        "coordinators (it should look like `...?block=3`). If you believe "
        "this is an error, contact the research team rather than guessing "
        "a block number."
    )


def render_thank_you():
    st.title("Thank you!")
    st.success(
        "Your responses have been recorded. You may now close this tab. "
        "Thank you for contributing to the FoodMedKG evaluation study."
    )


# --------------------------------------------------------------------------
# Main survey rendering.
# --------------------------------------------------------------------------
def render_survey(block_id: str, block_items: pd.DataFrame):
    st.title("FoodMedKG Evaluation Survey")
    st.caption(f"Block {block_id} — {len(block_items)} items")

    with st.form("survey_form", clear_on_submit=False):
        # --- Consent + demographic header (shown once, above the items) ---
        st.subheader("Before you begin")
        st.markdown(CONSENT_TEXT)
        consent_given = st.checkbox(
            "I have read the information above and agree to participate in this study."
        )

        col1, col2 = st.columns(2)
        with col1:
            year_of_study = st.selectbox(
                "Year of study",
                YEAR_OF_STUDY_OPTIONS,
                index=None,
                placeholder="Select year of study",
            )
        with col2:
            specialization = st.selectbox(
                "Specialization / field",
                SPECIALIZATION_OPTIONS,
                index=None,
                placeholder="Select specialization",
            )

        col3, col4, col5 = st.columns(3)
        with col3:
            gender = st.selectbox(
                "Gender",
                GENDER_OPTIONS,
                index=None,
                placeholder="Select gender",
            )
        with col4:
            # min_value is set below the real minimum (0) so the field
            # starts at an obviously-unset sentinel rather than at
            # value=None, which disables the +/- stepper buttons in
            # Streamlit until the user types a number manually.
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=MAX_AGE,
                value=0,
                step=1,
                help=f"Use +/- or type your age (must be at least {MIN_AGE}).",
            )
        with col5:
            english_level = st.selectbox(
                "Level of English",
                ENGLISH_LEVEL_OPTIONS,
                index=None,
                placeholder="Select level",
            )

        st.divider()
        st.subheader("Items to evaluate")

        # --- One rating block per item ---
        # index=None keeps radios unselected by default so we can detect
        # and reject incomplete submissions instead of silently recording
        # a false default answer.
        answers = {}
        for i, row in block_items.iterrows():
            st.markdown(f"**Item {i + 1} of {len(block_items)}**")
            relation_text = f"Food: **{row['food']}** → {row['type']}: **{row['target']}**"
            st.markdown(relation_text)
            if row.get("relation_text"):
                st.caption(row["relation_text"])
            if pd.notna(row.get("link")) and str(row.get("link")).strip():
                st.markdown(f"[Supporting citation]({row['link']}) — {row.get('citation', '')}")
            elif row.get("citation"):
                st.caption(f"Citation: {row['citation']}")

            correctness = st.radio(
                "Correctness of this relation",
                CORRECTNESS_OPTIONS,
                index=None,
                key=f"correctness_{row['item_id']}",
                horizontal=True,
            )
            oversimplified = st.radio(
                "Is this relation oversimplified?",
                OVERSIMPLIFIED_OPTIONS,
                index=None,
                key=f"oversimplified_{row['item_id']}",
                horizontal=True,
            )
            comment = st.text_area(
                "Optional comment",
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

        submitted = st.form_submit_button("Submit", use_container_width=True)

    if not submitted:
        return

    # --- Validation ---
    errors = []
    if not consent_given:
        errors.append("You must agree to the consent statement above to participate.")
    if not year_of_study:
        errors.append("Year of study is required.")
    if not specialization:
        errors.append("Specialization is required.")
    if not gender:
        errors.append("Gender is required.")
    if age < MIN_AGE:
        errors.append(f"Age is required and must be at least {MIN_AGE}.")
    if not english_level:
        errors.append("Level of English is required.")

    incomplete_items = [
        item_id
        for item_id, a in answers.items()
        if a["correctness"] is None or a["oversimplified"] is None
    ]
    if incomplete_items:
        errors.append(
            "The following items are missing a required answer: "
            + ", ".join(incomplete_items)
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
            "There was a problem saving your responses. Please do not "
            "close this tab — contact the study coordinators with the "
            f"following error: {exc}"
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
