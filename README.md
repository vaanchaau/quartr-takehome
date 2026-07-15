# SEC 10-K Fetcher

Given a list of companies, fetches each one's latest 10-K annual report from SEC EDGAR
and saves it as a PDF.

## How to run

```
uv run main.py
```

Reads `config.yaml`; each entry in `job_list` runs (or dry-runs, via `flag_dry_run`) one
job:
- `sec_company_tickers_list` — downloads SEC's ticker→CIK reference file and saves it as
  raw JSON plus a cleaned CSV (`ticker`, `cik_number`, `cik_str` as `CIK##########`,
  `company_name`, `tags`).
- `annual_sec_10k_report` — for each configured ticker, looks up its CIK from the latest
  saved CSV, finds its latest 10-K, and saves it as a PDF under
  `pdf_dir/YYYYMMDD/TICKER_accessionNumber.pdf`.

`annual_sec_10k_report` depends on `sec_company_tickers_list` having produced a CSV for
today (or a prior day) — that's why it runs second in `config.yaml`.

Run tests: `uv run pytest`. Format/lint: `uv run ruff format .` / `uv run ruff check .`.

## Process

**Hour 1 — exploration and skeleton.** 

Started by poking at the EDGAR APIs directly
(`company_tickers.json`, a company's submissions JSON) to see the actual shape of the
data before writing any code against it, and downloaded a sample filing to check what a
real 10-K page looks like. 

From there, drafted the overall solution shape (jobs config,
a common HTTP layer, an EDGAR-specific extraction module) and scaffolded the file
structure, starting with the shared `HttpClient`.

**Hour 2 — tickers pipeline.** 

Built the logic to fetch and save the ticker→CIK reference list. 

Treated it as static, cacheable data: it's fetched and saved once
(dated JSON + cleaned CSV) rather than re-fetched on every run, which also means the
list of companies to track can be changed by editing config, without needing to hit the
tickers endpoint again.

**Hours 3-4 — filings pipeline and hardening.** 

Implemented the CIK lookup → latest

10-K selection → HTML fetch → PDF render chain, then went back over the result:
unit tests around the parts most likely to silently break (latest-filing selection,
10-K/A exclusion, CSV tag-splitting), a self-review pass, and documentation.

> This project was built iteratively with Claude Code (Anthropic). Full prompt logs can be found [here](PROMPT_LOG.md).

## Reasoning & trade-offs

- **Input format: `config.yaml`.** A list of jobs, each carrying its own params
  (`user_agent`, `max_retries`, output directories, `companies`). This is the seam
  where a real service would swap in a dynamic company list instead of a static one.
- **HTML → PDF: Playwright (headless Chromium).** Chosen over WeasyPrint/pdfkit for
  fidelity on large, CSS-heavy filings. The plan was to `page.goto()` the filing URL
  directly for best fidelity on relative assets, but SEC's bot detection returns a 403
  ("Undeclared Automated Tool") to headless Chromium regardless of `User-Agent` —
  confirmed by testing, not assumed. The working approach instead fetches the HTML via
  `httpx` (which SEC does accept, given a descriptive `User-Agent`) and renders it from
  the string via `page.set_content()`. One browser is launched per job run and reused
  across companies, rather than one per PDF.
- **10-K/A amendments are excluded.** `filings.find_latest_10k` filters strictly to
  `form == "10-K"`. The assignment asks for the annual report itself, not a later
  correction to it.
- **CSV delimiter is `;`, not `,`.** Company names routinely contain commas (e.g.
  "Meta Platforms, Inc."), which would otherwise force quoting on nearly every row.
- **The ticker CSV is the source of truth for CIK lookup**, not a live re-fetch. Once
  `sec_company_tickers_list` has run for the day, `annual_sec_10k_report` reads CIKs
  from that saved CSV instead of hitting `company_tickers.json` again.
- **Concurrency is capped, not unlimited.** SEC asks for ~10 req/sec. Companies in
  `annual_sec_10k_report` are processed concurrently but bounded by
  `max_concurrency` (an `asyncio.Semaphore`), and one HTTP client and one browser are
  shared across the whole run rather than opened per company.
- **One company's failure doesn't abort the batch.** Per-company work is wrapped so a
  bad ticker, a missing 10-K, or an HTTP failure is caught and reported, while the rest
  of the batch keeps running and saving.

## What I deliberately skipped

- **Docker setup.** Not necessary to demonstrate the solution — `uv run` is enough to
  get this running, and containerizing it would have taken time away from the actual
  problem.
- **Exposing this as an API.** The task is a batch fetch/transform job, not a service
  that needs to answer requests on demand, so no HTTP server or endpoints were built.

Both were conscious cuts to keep the time budget on the data model and the solution
itself (EDGAR data shapes, the fetch/select/render pipeline, retry and concurrency
behavior) rather than on packaging or interface concerns that weren't part of what was
being evaluated.

## Known limitations

- `find_latest_10k` only looks at `filings.recent` in the submissions JSON, which is a
  rolling window of a company's most recent filings — older filings live in paginated
  files under `filings.files` that this function doesn't fetch. In practice a
  company's latest 10-K is always within `recent`, so this isn't a bug today, but it's
  a real limit if this function were ever repurposed to look further back in a
  company's history.
- Fetched JSON/CSV/PDF output under `files/sec-edgar/` is currently committed to git.
  It is intentionally placed to demonstrate the output.

## If this became the real Quartr service

- **Scheduling:** a cron/Airflow-style scheduler with an explicit DAG dependency
  (tickers job → 10-K job) instead of relying on `config.yaml`'s list order.
- **Incremental fetch:** skip re-rendering a company's PDF if its latest accession
  number hasn't changed since the last run (today it only skips re-downloading the
  ticker list if it already ran today; it doesn't yet dedup by filing).
- **Dedup:** check the target PDF path/accession number before re-fetching or
  re-rendering, and content-hash outputs to detect accidental duplicates.
- **Storage:** S3 (or equivalent) instead of local disk, keyed by
  `date/ticker/accessionNumber`, with the current dated-directory scheme mapping
  naturally onto prefixes.
- **Queue:** a per-company job queue (SQS/Pub-Sub) instead of in-process
  `asyncio.gather`, so retries, backpressure, and horizontal scaling don't all live in
  one process's memory.
- **Observability:** structured logging and metrics (success/failure counts per run,
  per-company latency) with alerting on job failure, replacing today's plain `print`
  statements.