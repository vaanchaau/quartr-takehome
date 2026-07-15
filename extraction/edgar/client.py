"""EDGAR HTTP client: fetches the SEC ticker-to-CIK reference file."""

from common.http_client import HttpClient

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


async def fetch_company_tickers(user_agent: str, *, max_retries: int) -> dict:
    """Download and parse the raw company_tickers.json payload from SEC EDGAR."""
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    async with HttpClient(headers, max_retries=max_retries) as client:
        response = await client.try_get_with_retry(TICKERS_URL)
        return response.json()
