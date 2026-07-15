from . import tickers


async def perform_sec_company_tickers_list(
    user_agent: str, *, max_retries: int, raw_json_dir: str, csv_dir: str
) -> None:
    await tickers.fetch_and_save_tickers(
        user_agent, max_retries=max_retries, raw_json_dir=raw_json_dir, csv_dir=csv_dir
    )


def perform_annual_sec_10k_report_job() -> None:
    print("hi")
