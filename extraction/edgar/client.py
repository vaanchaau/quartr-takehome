"""EDGAR HTTP client: fetches the SEC ticker-to-CIK reference file."""

from common.http_client import HttpClient

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/{cik}.json"
FILING_URL_TEMPLATE = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}"
)
FILING_TIMEOUT_SECONDS = 60.0


async def fetch_company_tickers(user_agent: str, *, max_retries: int) -> dict:
    """Download and parse the raw company_tickers.json payload from SEC EDGAR."""
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    async with HttpClient(headers, max_retries=max_retries) as client:
        response = await client.try_get_with_retry(TICKERS_URL)
        return response.json()


async def get_company_metadata(cik: str, *, user_agent: str, max_retries: int) -> dict:
    """Download and parse a company's submissions metadata from SEC EDGAR."""
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    url = SUBMISSIONS_URL_TEMPLATE.format(cik=cik)
    async with HttpClient(headers, max_retries=max_retries) as client:
        response = await client.try_get_with_retry(url)
        return response.json()


async def fetch_filing_html(
    cik: str, accession_number: str, primary_document: str, *, user_agent: str, max_retries: int
) -> str:
    """Download a filing's HTML content from SEC EDGAR. Filings can be large, so this
    uses a more generous timeout than the default."""
    headers = {"User-Agent": user_agent, "Accept": "text/html"}
    url = build_filing_url(cik, accession_number, primary_document)
    async with HttpClient(
        headers, max_retries=max_retries, timeout_seconds=FILING_TIMEOUT_SECONDS
    ) as client:
        response = await client.try_get_with_retry(url)
        return response.text


def build_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    return FILING_URL_TEMPLATE.format(
        cik=int(cik),
        accession_no_dashes=accession_number.replace("-", ""),
        primary_document=primary_document,
    )
