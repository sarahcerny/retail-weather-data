"""Collect monthly retail sales from the Census Bureau MRTS API.

Run from the repository root:
    uv run python scripts/fetch_census.py

Pulls unadjusted monthly sales (data_type_code SM) for five store categories,
January 2016 through December 2025, and saves the values before any cleaning.
The API key is read from census_key.txt, which must be listed in .gitignore.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/eits/mrts"
KEY_FILE = Path("census_key.txt")
OUTPUT = Path("data/raw/census_raw.csv")
USER_AGENT = (
    "STAT386-StudentProject/1.0 "
    "(educational data collection; limited requests; sarahmcerny@byu.edu)"
)
TIMEOUT_SECONDS = 30
POLITE_DELAY_SECONDS = 1.0

CATEGORIES = ["448", "451", "444", "452", "445"]
DATA_TYPE = "SM"  # monthly sales
SEASONAL_ADJ = "no"  # keep the seasonal pattern we want to study
START = "2016-01"
END = "2025-12"
EXPECTED_MONTHS = 120

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_key() -> str:
    """Read the API key from a local file that is not committed to GitHub."""
    if not KEY_FILE.exists():
        raise RuntimeError(f"Create {KEY_FILE} containing only your Census API key.")
    key = KEY_FILE.read_text().strip()
    if not key:
        raise RuntimeError(f"{KEY_FILE} is empty.")
    return key


def fetch_json(session: requests.Session, params: dict) -> list:
    """Fetch JSON and fail clearly. Error messages leave out the key."""
    try:
        response = session.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        # Census usually explains a 400 in the response body.
        # Remove the key before printing, just in case it is echoed back.
        message = exc.response.text[:300].replace(params.get("key", ""), "[KEY]")
        raise RuntimeError(
            f"Request failed with status {exc.response.status_code}: {message}"
        ) from None
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Request failed: {type(exc).__name__}") from None

def fetch_category(session: requests.Session, key: str, category: str) -> pd.DataFrame:
    """Pull one store category for the whole date range."""
    params = {
        "get": "cell_value,data_type_code,category_code,seasonally_adj,time_slot_id",
        "for": "us:*",
        "time": f"from {START} to {END}",
        "category_code": category,
        "data_type_code": DATA_TYPE,
        "seasonally_adj": SEASONAL_ADJ,
        "key": key,
    }
    rows = fetch_json(session, params)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.loc[:, ~df.columns.duplicated()]  # Census repeats filtered columns
    logging.info(
        "%s: %s rows back, %s distinct categories, months %s to %s",
        category,
        len(df),
        df["category_code"].nunique(),
        df["time"].min(),
        df["time"].max(),
    )
    # Filter again ourselves so we never trust the server's filtering blindly.
    return df[
        (df["category_code"] == category)
        & (df["data_type_code"] == DATA_TYPE)
        & (df["seasonally_adj"] == SEASONAL_ADJ)
        & (df["time_slot_id"] == "0")
        & (df["time"] >= START)
        & (df["time"] <= END)
    ]


def validate(df: pd.DataFrame) -> None:
    """Fail loudly if the pull is not what we expect."""
    assert len(df) > 0, "No rows returned"
    found = set(df["category_code"])
    assert found == set(CATEGORIES), (
        f"Missing: {set(CATEGORIES) - found}, unexpected: {found - set(CATEGORIES)}"
    )
    assert (df["data_type_code"] == DATA_TYPE).all(), "Unexpected data type"
    assert (df["seasonally_adj"] == SEASONAL_ADJ).all(), "Unexpected adjustment"
    assert not df.duplicated(["category_code", "time"]).any(), "Duplicate months"
    counts = df.groupby("category_code")["time"].nunique()
    assert (counts == EXPECTED_MONTHS).all(), f"Month counts are off:\n{counts}"
    print("All checks passed")


def main() -> None:
    key = read_key()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    frames = []
    for number, category in enumerate(CATEGORIES, start=1):
        if number > 1:
            time.sleep(POLITE_DELAY_SECONDS)
        logging.info("Fetching category %s (%s/%s)", category, number, len(CATEGORIES))
        frames.append(fetch_category(session, key, category))

    df = pd.concat(frames, ignore_index=True)
    df["retrieved"] = date.today().isoformat()  # data gets revised, so record when

    validate(df)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    logging.info("Saved %s raw rows to %s", len(df), OUTPUT)


if __name__ == "__main__":
    main()