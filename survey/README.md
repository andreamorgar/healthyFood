# FoodMedKG Human Evaluation Survey

A minimal Streamlit app for collecting human evaluation of FoodMedKG
relations from nutrition/dietetics/medicine students, split into rotating
blocks so each respondent only rates a subset of the item pool. Responses
are stored in a Google Sheet (there is no local persistence, since
Streamlit Community Cloud's filesystem is ephemeral and not shared across
sessions or instances).

## Project structure

```
survey/
├── app.py                       # Main Streamlit app
├── items.csv                    # Item pool with block assignments (sample data — replace with the real pool)
├── requirements.txt             # App dependencies
├── .streamlit/
│   └── secrets.toml.example     # Template for local secrets (copy to secrets.toml, do not commit the real one)
├── analysis/
│   └── analyze_responses.py     # Standalone script: pulls responses from Sheets, computes agreement stats
└── README.md
```

## 1. `items.csv` format

Columns: `item_id, block_id, type, food, target, relation_text, citation, link`

- `type` is one of `disease`, `aging`, `cooking_method`.
- `target` is the disease name / aging indicator / cooking method name.
- `link` may be empty; if present it is rendered as a clickable citation link.
- `block_id` determines which respondents see which items — assign block
  numbers so that each sub-group of students gets a distinct `?block=N`
  link and no one is expected to rate the entire pool.

The included `items.csv` is **sample/placeholder data** (blocks 1–2, a
handful of rows across all three `type` values) so the app is runnable
immediately. Replace it with the real item pool before distributing links.

## 2. Block routing

Respondents are sent a link like:

```
https://<your-app>.streamlit.app/?block=3
```

The app reads the `block` query parameter and filters `items.csv` to
`block_id == block`. If the parameter is missing or doesn't match any
block, the app shows a short landing screen asking the respondent to use
their assigned link — it never guesses or randomly assigns a block. Block
links must be distributed manually to each sub-group of students.

## 3. Setting up the Google Sheet + service account

1. **Create the Google Sheet** that will store responses. Note its exact
   name (or switch the app to open by key/ID — see the note in `app.py`
   and `analysis/analyze_responses.py` where `SPREADSHEET_NAME` is
   defined). No worksheet setup is required — the app creates the
   `responses` worksheet and header row automatically on first submission
   if it doesn't already exist.

2. **Create a Google Cloud service account:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/),
     create or select a project.
   - Enable the **Google Sheets API** and **Google Drive API** for that
     project (APIs & Services → Library).
   - Go to APIs & Services → Credentials → Create Credentials → Service
     Account. Give it any name (e.g. `foodmedkg-survey`).
   - Open the new service account → Keys → Add Key → Create new key →
     JSON. This downloads a JSON key file — **keep it secret**, it grants
     access to anything shared with the service account.

3. **Share the Google Sheet** with the service account: open the Sheet →
   Share → paste the service account's `client_email` (found in the JSON
   key, looks like `xxx@yyy.iam.gserviceaccount.com`) → give it **Editor**
   access.

## 4. Local setup

```bash
cd survey
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the secrets template and fill it in with values from the downloaded
JSON key:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-gcp-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-gcp-project-id.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-gcp-project-id.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

**Never commit `.streamlit/secrets.toml`** — it is already excluded via
`.gitignore` at the repo root; double-check before pushing.

Update `SPREADSHEET_NAME` in `app.py` to match your real Sheet's name, and
replace `CONSENT_TEXT` with the final consent/info wording before
distributing real links.

Run locally:

```bash
streamlit run app.py
```

Then open `http://localhost:8501/?block=1` to test a specific block (block
`1` and `2` exist in the sample `items.csv`).

## 5. Deploying to Streamlit Community Cloud

1. Push this repository (or at least the `survey/` folder) to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) → New app →
   point it at this repo, with **main file path** set to `survey/app.py`
   (adjust if you deploy `survey/` as its own repo, in which case use
   `app.py`).
3. Under **Advanced settings → Secrets**, paste the same contents as your
   local `.streamlit/secrets.toml` (the `[gcp_service_account]` table).
   This is the production equivalent of the local secrets file — Streamlit
   Community Cloud exposes it to the app as `st.secrets` at runtime.
4. Deploy. Once live, construct one link per block for distribution, e.g.:
   - `https://<your-app>.streamlit.app/?block=1`
   - `https://<your-app>.streamlit.app/?block=2`
   - ... one per sub-group of students.

Streamlit Community Cloud's filesystem is ephemeral and reset on every
redeploy/restart, and multiple sessions may run on different underlying
instances — this is why the app never writes to local disk and uses
Google Sheets as the single source of truth for all responses.

## 6. Running the analysis script

`analysis/analyze_responses.py` is a standalone script, run locally (not
part of the deployed app), that pulls all rows from the `responses`
worksheet and computes:

- A per-item summary: `item_id, type, food, target, % Agree, % Disagree,
  % Not sure, % flagged oversimplified, number of raters`
- An overall Fleiss' kappa (categories: Agree / Disagree / Not sure) across
  items that share the same (modal) number of raters, using
  `statsmodels.stats.inter_rater.fleiss_kappa` if installed, or a direct
  implementation otherwise.

Setup:

```bash
cd survey/analysis
pip install statsmodels pandas gspread google-auth
```

The script reuses credentials from `../.streamlit/secrets.toml` by default
(the same file used by the app locally). If running on Python < 3.11,
also `pip install tomli` (used as the `tomllib` fallback for reading that
file). Alternatively, drop a raw service-account JSON key at
`analysis/service_account.json` (already covered by `.gitignore`).

Update `SPREADSHEET_NAME` at the top of the script to match `app.py`, then
run:

```bash
python analyze_responses.py
```

This prints the summary table and overall kappa to the console and saves
the summary table to `analysis/summary.csv`.

## Notes on privacy

- No names or emails are collected. Each respondent gets a random UUID4
  (`respondent_id`) generated client-side at session start, used only to
  group that session's rows together.
- Demographic fields collected are: year of study, specialization,
  gender, age, and level of English — all from closed option lists except
  age (a plain number). No other identifying information is collected.
- After a successful submit, the app shows a thank-you screen and
  disables the form for that session (via `st.session_state`) to avoid the
  common case of an accidental duplicate submission on page reload. A
  respondent who deliberately opens a fresh session/tab can still submit
  again — this is accepted as out of scope per the study design.
