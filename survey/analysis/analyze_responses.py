"""
FoodMedKG survey — response analysis.

Standalone script (run locally, not part of the deployed Streamlit app)
that pulls the "responses" worksheet from the study's Google Sheet and
computes per-item agreement statistics plus an overall Fleiss' kappa.

Usage:
    python analyze_responses.py

Requires the same service-account credentials used by the app. By default
this script looks for them at ../.streamlit/secrets.toml (the same file
used locally by the Streamlit app) so you don't need a second copy of the
key. Alternatively, point CREDENTIALS_PATH at a raw service-account JSON
file downloaded from Google Cloud.
"""

import sys
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

# --------------------------------------------------------------------------
# Configuration — adjust to match your deployment.
# --------------------------------------------------------------------------
SPREADSHEET_NAME = "FoodMedKG_Survey_Responses"  # placeholder, must match app.py
RESPONSES_WORKSHEET = "responses"

# Where to find service-account credentials. Tries a plain JSON key file
# first, then falls back to the Streamlit secrets.toml used by the app.
CREDENTIALS_JSON_PATH = Path(__file__).parent / "service_account.json"
SECRETS_TOML_PATH = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"

CORRECTNESS_CATEGORIES = ["Agree", "Disagree", "Not sure"]

OUTPUT_CSV_PATH = Path(__file__).parent / "summary.csv"


def load_credentials() -> Credentials:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    if CREDENTIALS_JSON_PATH.exists():
        return Credentials.from_service_account_file(str(CREDENTIALS_JSON_PATH), scopes=scopes)
    if SECRETS_TOML_PATH.exists():
        with open(SECRETS_TOML_PATH, "rb") as f:
            secrets = tomllib.load(f)
        return Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=scopes)
    raise FileNotFoundError(
        "No credentials found. Provide either "
        f"{CREDENTIALS_JSON_PATH} (a service-account JSON key) or "
        f"{SECRETS_TOML_PATH} (the app's secrets.toml)."
    )


def load_responses() -> pd.DataFrame:
    client = gspread.authorize(load_credentials())
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(RESPONSES_WORKSHEET)
    records = worksheet.get_all_records()
    if not records:
        raise ValueError("The 'responses' worksheet is empty — nothing to analyze.")
    return pd.DataFrame(records)


def build_rating_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """One row per item_id, one column per category, cell = count of raters
    who chose that category for that item — the input shape fleiss_kappa
    expects."""
    counts = (
        df.groupby(["item_id", "correctness"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=CORRECTNESS_CATEGORIES, fill_value=0)
    )
    return counts


def fleiss_kappa(rating_matrix: pd.DataFrame) -> float:
    """Compute Fleiss' kappa, preferring statsmodels' implementation and
    falling back to a direct implementation if statsmodels is unavailable."""
    try:
        from statsmodels.stats.inter_rater import fleiss_kappa as sm_fleiss_kappa

        return float(sm_fleiss_kappa(rating_matrix.to_numpy(), method="fleiss"))
    except ImportError:
        return _fleiss_kappa_manual(rating_matrix.to_numpy())


def _fleiss_kappa_manual(table) -> float:
    """Direct implementation of Fleiss' kappa (used only if statsmodels is
    not installed). table: (n_items, n_categories) array of counts."""
    n_items, n_categories = table.shape
    n_raters = table.sum(axis=1)
    if not (n_raters == n_raters[0]).all():
        raise ValueError("Fleiss' kappa requires the same number of raters per item.")
    n = n_raters[0]

    # Per-item agreement.
    p_i = ((table * (table - 1)).sum(axis=1)) / (n * (n - 1))
    p_bar = p_i.mean()

    # Per-category proportion across all items/raters.
    p_j = table.sum(axis=0) / (n_items * n)
    p_e_bar = (p_j**2).sum()

    if p_e_bar == 1:
        return 1.0
    return (p_bar - p_e_bar) / (1 - p_e_bar)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for item_id, group in df.groupby("item_id"):
        n_raters = len(group)
        correctness_counts = group["correctness"].value_counts(normalize=True) * 100
        oversimplified_pct = (group["oversimplified"] == "Yes").mean() * 100
        rows.append(
            {
                "item_id": item_id,
                "type": group["type"].iloc[0],
                "food": group["food"].iloc[0],
                "target": group["target"].iloc[0],
                "pct_agree": round(correctness_counts.get("Agree", 0.0), 1),
                "pct_disagree": round(correctness_counts.get("Disagree", 0.0), 1),
                "pct_not_sure": round(correctness_counts.get("Not sure", 0.0), 1),
                "pct_oversimplified": round(oversimplified_pct, 1),
                "n_raters": n_raters,
            }
        )
    summary = pd.DataFrame(rows).sort_values("item_id").reset_index(drop=True)
    return summary


def main():
    print(f"Loading responses from Google Sheet '{SPREADSHEET_NAME}'...")
    df = load_responses()
    print(f"Loaded {len(df)} response rows across {df['item_id'].nunique()} items.")

    summary = build_summary(df)
    print("\nPer-item summary:")
    print(summary.to_string(index=False))

    summary.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"\nSaved summary table to {OUTPUT_CSV_PATH}")

    # Fleiss' kappa requires a constant number of raters per item; restrict
    # to items with the modal rater count so the overall figure is valid.
    rating_matrix = build_rating_matrix(df)
    rater_counts = rating_matrix.sum(axis=1)
    modal_count = rater_counts.mode().iloc[0]
    eligible = rating_matrix[rater_counts == modal_count]
    dropped = rating_matrix[rater_counts != modal_count]

    if dropped.shape[0]:
        print(
            f"\nNote: {dropped.shape[0]} item(s) excluded from overall kappa "
            f"because they don't have the modal rater count ({modal_count}): "
            f"{list(dropped.index)}"
        )

    if eligible.shape[0] < 2:
        print("\nNot enough items with a consistent rater count to compute overall kappa.")
        sys.exit(0)

    kappa = fleiss_kappa(eligible)
    print(f"\nOverall Fleiss' kappa (correctness, {modal_count} raters/item, "
          f"{eligible.shape[0]} items): {kappa:.3f}")


if __name__ == "__main__":
    main()
