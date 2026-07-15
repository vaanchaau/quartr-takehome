"""EDGAR HTTP client: gets SEC EDGAR ticker, submissions, and filing data.

Callers build one HttpClient (via build_client) per job run and pass it into every
call below, so a run's requests share a single connection pool instead of opening a
fresh connection per call.
"""

from common.http_client import HttpClient

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/{cik}.json"
FILING_URL_TEMPLATE = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}"
)
FILING_TIMEOUT_SECONDS = 60.0


def build_client(user_agent: str, *, max_retries: int) -> HttpClient:
    """Build a shared EDGAR HTTP client. Uses the filing-document timeout throughout
    so one client can be reused for both small JSON calls and large filing downloads."""
    headers = {"User-Agent": user_agent}
    return HttpClient(headers, max_retries=max_retries, timeout_seconds=FILING_TIMEOUT_SECONDS)


async def get_company_tickers(client: HttpClient) -> dict:
    """Download and parse the raw company_tickers.json payload from SEC EDGAR."""
    response = await client.try_get_with_retry(TICKERS_URL)
    return response.json()


async def get_company_metadata(client: HttpClient, cik: str) -> dict:
    """Download and parse a company's submissions metadata from SEC EDGAR."""
    url = SUBMISSIONS_URL_TEMPLATE.format(cik=cik)
    response = await client.try_get_with_retry(url)
    return response.json()


async def get_filing_html(
    client: HttpClient, cik: str, accession_number: str, primary_document: str
) -> str:
    """Download a filing's HTML content from SEC EDGAR."""
    url = build_filing_url(cik, accession_number, primary_document)
    response = await client.try_get_with_retry(url)
    return response.text


def build_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    return FILING_URL_TEMPLATE.format(
        cik=int(cik),
        accession_no_dashes=accession_number.replace("-", ""),
        primary_document=primary_document,
    )
