import asyncio
import sys

from playwright.async_api import Browser

from common.http_client import HttpClient
from common.pdf import launch_browser

from . import client, filings, tickers


async def perform_sec_company_tickers_list(
    user_agent: str, *, max_retries: int, raw_json_dir: str, csv_dir: str
) -> None:
    await tickers.get_and_save_tickers(
        user_agent, max_retries=max_retries, raw_json_dir=raw_json_dir, csv_dir=csv_dir
    )


async def perform_annual_sec_10k_report_job(
    companies: list[str],
    *,
    user_agent: str,
    max_retries: int,
    tickers_csv_dir: str,
    pdf_dir: str,
    max_concurrency: int,
) -> None:
    """Look up each configured ticker's CIK from the latest saved tickers CSV and
    save its latest 10-K as PDF. Companies are processed concurrently, capped at
    max_concurrency so the job doesn't burst past SEC's rate limit, and one
    company's failure doesn't stop the others from being saved."""
    ticker_index = tickers.load_latest_tickers(tickers_csv_dir)
    semaphore = asyncio.Semaphore(max_concurrency)
    async with (
        client.build_client(user_agent, max_retries=max_retries) as http_client,
        launch_browser() as browser,
    ):
        errors = await asyncio.gather(
            *(
                _save_company_10k(ticker, ticker_index, http_client, browser, pdf_dir, semaphore)
                for ticker in companies
            )
        )
    _log_errors(errors)


async def _save_company_10k(
    ticker: str,
    ticker_index: dict[str, dict],
    http_client: HttpClient,
    browser: Browser,
    pdf_dir: str,
    semaphore: asyncio.Semaphore,
) -> str | None:
    """Save one company's latest 10-K as PDF. Returns an error message on failure
    instead of raising, so one company's failure doesn't cancel the others."""
    async with semaphore:
        try:
            row = ticker_index[ticker.upper()]
            company_metadata = await client.get_company_metadata(http_client, row["cik_str"])
            await filings.get_and_save_latest_10k_pdf(
                http_client,
                browser,
                row["cik_number"],
                row["ticker"],
                company_metadata,
                pdf_dir=pdf_dir,
            )
            return None
        except Exception as exc:
            return f"{ticker}: {exc}"


def _log_errors(errors: list[str | None]) -> None:
    failures = [error for error in errors if error is not None]
    if not failures:
        return
    print(f"{len(failures)} of {len(errors)} companies failed:", file=sys.stderr)
    for failure in failures:
        print(f"  {failure}", file=sys.stderr)
