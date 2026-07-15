import asyncio

from . import client, filings, tickers


async def perform_sec_company_tickers_list(
    user_agent: str, *, max_retries: int, raw_json_dir: str, csv_dir: str
) -> None:
    await tickers.fetch_and_save_tickers(
        user_agent, max_retries=max_retries, raw_json_dir=raw_json_dir, csv_dir=csv_dir
    )


async def perform_annual_sec_10k_report_job(
    companies: list[str],
    *,
    user_agent: str,
    max_retries: int,
    tickers_csv_dir: str,
    pdf_dir: str,
) -> None:
    """Look up each configured ticker's CIK from the latest saved tickers CSV and
    save its latest 10-K as PDF, processing all companies concurrently."""
    ticker_index = tickers.load_latest_tickers(tickers_csv_dir)
    await asyncio.gather(
        *(
            _save_company_10k(
                ticker_index[ticker.upper()],
                user_agent=user_agent,
                max_retries=max_retries,
                pdf_dir=pdf_dir,
            )
            for ticker in companies
        )
    )


async def _save_company_10k(row: dict, *, user_agent: str, max_retries: int, pdf_dir: str) -> None:
    company_metadata = await client.get_company_metadata(
        row["cik_str"], user_agent=user_agent, max_retries=max_retries
    )
    await filings.fetch_and_save_latest_10k_pdf(
        row["cik_number"],
        row["ticker"],
        company_metadata,
        user_agent=user_agent,
        max_retries=max_retries,
        pdf_dir=pdf_dir,
    )
