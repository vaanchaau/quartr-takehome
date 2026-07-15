"""Fetch SEC's ticker-to-CIK reference file and save it as raw JSON and CSV."""

import csv
import datetime
import json
import os
import re

from .client import fetch_company_tickers

RAW_JSON_FILENAME = "company_tickers.json"
CSV_FILENAME = "tickers.csv"
CSV_DELIMITER = ";"
CSV_FIELDS = ("ticker", "cik_number", "cik_str", "company_name", "tags")
TAG_SUFFIX_PATTERN = re.compile(r"\s*/([^/]*)/?$")


async def fetch_and_save_tickers(
    user_agent: str, *, max_retries: int, raw_json_dir: str, csv_dir: str
) -> None:
    """Fetch the ticker list from EDGAR unless today's raw JSON already exists,
    then save it as CSV."""
    raw_json_path = _raw_json_path(raw_json_dir)
    if not os.path.exists(raw_json_path):
        tickers = await fetch_company_tickers(user_agent, max_retries=max_retries)
        raw_json_path = _save_raw_json(tickers, raw_json_dir)
    _save_tickers_csv(raw_json_path, csv_dir)


def _raw_json_path(raw_json_dir: str) -> str:
    return os.path.join(raw_json_dir, _dated_filename(RAW_JSON_FILENAME))


def _save_raw_json(tickers: dict, raw_json_dir: str) -> str:
    os.makedirs(raw_json_dir, exist_ok=True)

    path = _raw_json_path(raw_json_dir)
    with open(path, "w") as f:
        json.dump(tickers, f)
    return path


def _save_tickers_csv(raw_json_path: str, csv_dir: str) -> None:
    tickers = _load_tickers_json(raw_json_path)
    os.makedirs(csv_dir, exist_ok=True)
    path = os.path.join(csv_dir, _dated_filename(CSV_FILENAME))
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=CSV_DELIMITER)
        writer.writeheader()
        for entry in tickers.values():
            writer.writerow(_to_csv_row(entry))


def _load_tickers_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def load_latest_tickers(csv_dir: str) -> dict[str, dict]:
    """Load the most recently saved tickers CSV, indexed by uppercase ticker."""
    path = _latest_csv_path(csv_dir)
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
        return {row["ticker"].upper(): row for row in reader}


def _latest_csv_path(csv_dir: str) -> str:
    filenames = sorted(f for f in os.listdir(csv_dir) if f.endswith(CSV_FILENAME))
    return os.path.join(csv_dir, filenames[-1])


def _to_csv_row(entry: dict) -> dict:
    company_name, tags = _split_company_name_and_tag(entry["title"])
    return {
        "ticker": entry["ticker"],
        "cik_number": entry["cik_str"],
        "cik_str": _format_cik(entry["cik_str"]),
        "company_name": company_name,
        "tags": tags,
    }


def _format_cik(cik: int) -> str:
    return f"CIK{cik:010d}"


def _split_company_name_and_tag(title: str) -> tuple[str, str]:
    match = TAG_SUFFIX_PATTERN.search(title)
    if match:
        return TAG_SUFFIX_PATTERN.sub("", title), match.group(1)
    return title, ""


def _dated_filename(filename: str) -> str:
    date_prefix = datetime.date.today().strftime("%Y%m%d")
    return f"{date_prefix}_{filename}"
