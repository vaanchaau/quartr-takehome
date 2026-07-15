"""Entry point: load config and run each configured job."""

import sys

import yaml

from extraction.edgar import perform_annual_sec_10k_report_job, perform_sec_company_tickers_list

CONFIG_PATH = "config.yaml"


def main() -> None:
    config = _load_config(CONFIG_PATH)
    for job in config["job_list"]:
        _run_job(job["job_name"])
    return


def _load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _run_job(job_name: str) -> None:
    match job_name:
        case "sec_company_tickers_list":
            perform_sec_company_tickers_list()
        case "annual_sec_10k_report":
            perform_annual_sec_10k_report_job()
        case _:
            pass


if __name__ == "__main__":
    sys.exit(main())
