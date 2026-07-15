# Quartr Coding Assignment — Data Automation (Documents)

## Goal
Given a list of companies, fetch each company's **latest 10-K** annual report from
SEC EDGAR and save it as a **PDF**. This is the basis for a service that fetches reports
and exposes them to other teams at Quartr.

Companies (defaults): Apple, Meta, Alphabet, Amazon, Netflix, Goldman Sachs.

## Constraints & deliverables
- **Python** (required).
- Deliver: source code + instructions to run + a prompt log if any AI tool was used.
- API endpoint / Docker are **optional** (fetch + convert is sufficient).
- Input format is the candidate's choice — decide and **motivate** it.
- Evaluated on: coding skill, problem-solving, and ability to explain reasoning.
  Heavy delegation to all-in-one libraries reduces discussion value, so implement the
  SEC-fetching logic myself rather than using a `sec-edgar` wrapper.

## Approach — use EDGAR structured JSON APIs (not scraping)
Three hops per company:
1. **Ticker -> CIK**: download `https://www.sec.gov/files/company_tickers.json`, build a
   ticker->CIK map, zero-pad CIK to 10 digits.
2. **CIK -> latest 10-K**: GET `https://data.sec.gov/submissions/CIK##########.json`,
   filter `form == "10-K"` (decide whether to exclude `10-K/A` amendments and motivate),
   sort by `filingDate`, take newest. Read its `accessionNumber` and `primaryDocument`.
3. **Download filing**: `https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes_removed}/{primaryDocument}`
   then convert that HTML to PDF.

## Key decisions to make and defend
- **HTML -> PDF conversion**: Playwright (headless Chromium) `page.pdf()` navigating
  directly to the filing URL gives best fidelity and resolves relative images/CSS.
  Lighter alternatives (WeasyPrint, pdfkit/wkhtmltopdf) can mangle large filings.
  Pick one and be ready to argue the trade-off.
- **Input format**: small config (JSON/YAML) or CLI args, keyed by ticker, with the 6 as
  defaults — the seam where a real service would take a dynamic company list.

## Pitfalls (must handle)
- SEC requires a descriptive `User-Agent` header (e.g. "Van Chau Dao vaanchaau@gmail.com")
  or requests get 403.
- Respect ~10 req/sec rate limit — add throttle + retry/backoff.
- CIK zero-padding; accession number has dashes in JSON but not in the archive path.
- Choose "latest" deterministically; handle "no 10-K found" gracefully.

## Suggested structure
- `edgar_client.py` — HTTP session, headers, rate limiting, retry/backoff
- `filings.py` — resolve ticker->CIK, find latest 10-K, build document URL
- `pdf.py` — HTML -> PDF conversion
- `main.py` — orchestrate, save to `output/{TICKER}_{filingDate}.pdf`
- `tests/` — 1-2 unit tests with mocked JSON (CIK resolution, latest-filing selection)
- `README.md` — how to run + reasoning/trade-offs + a short "if this became the real
  Quartr service" section (scheduling, incremental fetch, dedup, S3 storage, a queue,
  observability)

## Notes on implementation
- Keep it simple.
- Each function must only perform one action.
- All input and output configurations only exist in YAML files. No inline, hard coded value accepted.
- Solution is provided strictly in the scope of the prompt and with confirmation from user. No over deliver or generating files outside of the scope of the prompt.
- Keep a prompt log of any AI assistance.
