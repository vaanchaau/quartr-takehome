## How to run
```
uv run main.py
```
Reads `config.yaml`; each entry in `job_list` runs (or dry-runs) one job.

The one caveat: EDGAR's recent block only holds a rolling window of the most recent filings (older ones move to paginated files under filings.files), so if a company's latest 10-K
somehow fell outside that window this function wouldn't see it — but that's a data-availability limit, not a position-based bug in the code. In practice, a company's most recent  
10-K is always within recent.