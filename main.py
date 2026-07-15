"""Entry point: load config and run each configured job."""

import asyncio
import sys

import yaml

from extraction.edgar import perform_annual_sec_10k_report_job, perform_sec_company_tickers_list

CONFIG_PATH = "config.yaml"


def main() -> None:
    asyncio.run(_run_jobs())
    return


async def _run_jobs() -> None:
    config = _load_config(CONFIG_PATH)
    for job in config["job_list"]:
        await _run_job(job)


def _load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


async def _run_job(job: dict) -> None:
    if job["flag_dry_run"]:
        print(f"Dry run... {job['job_name']}")
        return

    match job["job_name"]:
        case "sec_company_tickers_list":
            await perform_sec_company_tickers_list(
                job["user_agent"],
                max_retries=job["max_retries"],
                raw_json_dir=job["raw_json_dir"],
                csv_dir=job["csv_dir"],
            )
        case "annual_sec_10k_report":
            await perform_annual_sec_10k_report_job(
                job["companies"],
                user_agent=job["user_agent"],
                max_retries=job["max_retries"],
                tickers_csv_dir=job["tickers_csv_dir"],
                pdf_dir=job["pdf_dir"],
            )
        case _:
            pass


if __name__ == "__main__":
    sys.exit(main())
