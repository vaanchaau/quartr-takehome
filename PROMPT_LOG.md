# Prompt Log

This project was built iteratively with Claude Code (Anthropic). Log of the prompts that drove each step, in order, condensed to what was asked and what changed.

1. "add a main function to extraction/edgar called 'perform_annual_sec_10k_report_job'... print hi... in root main, load config from yaml, if job_name is annual_sec_10k_report run that job" — first job dispatch wiring in `main.py`.
2. "export the two function in edgar main in init, and import the actions to the root main.py" — wired `extraction/edgar/__init__.py` exports.
3. "change the http client to a class with try get method expose, and the try get with retry method. the timeout and retry number, and backoff seconds has default value" — `common/http_client.py`'s `HttpClient` class.
4. "implement a client in extraction edgar client to get the tickers request using the http client in common" — `client.fetch_company_tickers`.
5. "implement the tickers.py that fetch from client and take json save to csv format... json in files/sec-edgar/raw/, csv in files/sec-edgar/tickers" — `tickers.py`'s fetch/save pipeline; added those paths to `config.yaml`.
6. "perform_sec_company_tickers_list should call the tickers now" — wired the job to `tickers.fetch_and_save_tickers`; made `main.py`'s job dispatch async.
7. "change column name title to company_name; undo quotation marks for names like 'Meta Platforms, Inc.'; strip trailing '/DE' into a new tags column" — switched CSV delimiter to `;` (avoids quoting commas), added tag-suffix splitting.
8. "generalize the function... any string after the trailing '/'" — generalized the tag regex from `/DE`-only to any suffix (`ADR`, `OH`, etc.).
9. "fetch_and_save_tickers should check if json file exists before fetching" — skip re-fetching if today's dated raw JSON is already on disk.
10. "why not get from files/sec-edgar/tickers, they're already formatted... get the latest csv for cik lookup" — `tickers.load_latest_tickers` reads from the saved CSV instead of re-fetching from EDGAR.
11. "create a function in edgar client called get company metadata... given cik_string" — `client.get_company_metadata`.
12. "write a function in filings that goes through a dict of company metadata and fish out the latest 10k report" — `filings.find_latest_10k`.
13. "make a readme of the progress so far... add the caveat" — first README draft.
14. "fetch_filing_html should receive cik number, and other input to make the url" — changed signature to build the URL from `cik`/`accession_number`/`primary_document`.
15. "now filings call the fetch and take html result to pdf" — added `common/pdf.py` (`html_to_pdf` via `page.set_content`) and `filings.fetch_and_save_latest_10k_pdf`.
16. "switch to direct navigation instead" → tried `page.goto()` directly; **discovered SEC returns a 403 ("Undeclared Automated Tool") to headless Chromium regardless of User-Agent** — reverted to the fetch-then-render approach with the finding documented in `common/pdf.py`.
17. "wire perform_annual_sec_10k_report_job to use this and save the latest 10k of 5 companies at the same time" — full job wiring with `asyncio.gather`.
18. "i would like ... all pdf under a folder of current run date... filename should be ticker instead of company name" — `pdf_dir/YYYYMMDD/TICKER_accessionNumber.pdf`.
19. "review the entire codebase against the given task and assess the solution as a senior data engineer" — produced a written assessment (missing tests, missing prompt log, thin README, ungraceful batch failure handling, no throttle, no connection/browser reuse, committed generated data, `Retry-After` date-format edge case, lost 10-K/A rationale comment).