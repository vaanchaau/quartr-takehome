"""Resolve a company's latest 10-K filing from its EDGAR submissions metadata,
convert it to PDF, and save it."""

import datetime
import os

from playwright.async_api import Browser

from common.http_client import HttpClient
from common.pdf import html_to_pdf

from . import client

TEN_K_FORM = "10-K"
FILING_FIELDS = ("form", "accessionNumber", "primaryDocument", "filingDate")


class NoTenKFoundError(Exception):
    """Raised when a company's metadata has no 10-K filings on record."""


def find_latest_10k(company_metadata: dict) -> dict[str, str]:
    """Return the newest 10-K filing's metadata from a company's EDGAR submissions payload.

    Filters strictly to form == "10-K", excluding 10-K/A amendments: the assignment
    asks for the annual report itself, not a later correction to it."""
    ten_ks = _ten_k_filings(company_metadata["filings"]["recent"])
    if not ten_ks:
        raise NoTenKFoundError("no 10-K filings found in company metadata")
    return max(ten_ks, key=lambda filing: filing["filingDate"])


def _ten_k_filings(recent: dict) -> list[dict[str, str]]:
    rows = zip(*(recent[field] for field in FILING_FIELDS))
    return [dict(zip(FILING_FIELDS, row)) for row in rows if row[0] == TEN_K_FORM]


async def get_and_save_latest_10k_pdf(
    http_client: HttpClient,
    browser: Browser,
    cik: str,
    ticker: str,
    company_metadata: dict,
    *,
    pdf_dir: str,
) -> str:
    """Find a company's latest 10-K, render it to PDF, and save it under pdf_dir in a
    subdirectory named for today's run date. Returns the saved file's path."""
    filing = find_latest_10k(company_metadata)
    html = await client.get_filing_html(
        http_client, cik, filing["accessionNumber"], filing["primaryDocument"]
    )
    pdf_bytes = await html_to_pdf(browser, html)
    return _save_pdf(pdf_bytes, ticker, filing["accessionNumber"], pdf_dir)


def _save_pdf(pdf_bytes: bytes, ticker: str, accession_number: str, pdf_dir: str) -> str:
    run_dir = _dated_run_dir(pdf_dir)
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, _pdf_filename(ticker, accession_number))
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


def _dated_run_dir(pdf_dir: str) -> str:
    return os.path.join(pdf_dir, datetime.date.today().strftime("%Y%m%d"))


def _pdf_filename(ticker: str, accession_number: str) -> str:
    return f"{ticker.upper()}_{accession_number}.pdf"
