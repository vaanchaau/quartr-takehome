import pytest

from extraction.edgar.filings import NoTenKFoundError, find_latest_10k


def _company_metadata(rows: list[tuple[str, str, str, str]]) -> dict:
    """Build a fake submissions payload. Each row is
    (form, accessionNumber, primaryDocument, filingDate)."""
    fields = ("form", "accessionNumber", "primaryDocument", "filingDate")
    columns = zip(*rows) if rows else ([],) * len(fields)
    return {"filings": {"recent": dict(zip(fields, columns))}}


def test_find_latest_10k_picks_newest_filing_date():
    metadata = _company_metadata(
        [
            ("10-K", "0000320193-23-000106", "aapl-2023.htm", "2023-11-03"),
            ("10-K", "0000320193-25-000079", "aapl-2025.htm", "2025-10-31"),
            ("10-K", "0000320193-24-000123", "aapl-2024.htm", "2024-11-01"),
        ]
    )

    filing = find_latest_10k(metadata)

    assert filing["filingDate"] == "2025-10-31"
    assert filing["accessionNumber"] == "0000320193-25-000079"


def test_find_latest_10k_excludes_10ka_amendments():
    metadata = _company_metadata(
        [
            ("10-K", "0000320193-24-000123", "aapl-2024.htm", "2024-11-01"),
            ("10-K/A", "0000320193-25-000001", "aapl-2025a.htm", "2025-12-01"),
        ]
    )

    filing = find_latest_10k(metadata)

    assert filing["form"] == "10-K"
    assert filing["filingDate"] == "2024-11-01"


def test_find_latest_10k_raises_when_no_10k_present():
    metadata = _company_metadata([("10-Q", "0000320193-25-000050", "aapl-q3.htm", "2025-08-01")])

    with pytest.raises(NoTenKFoundError):
        find_latest_10k(metadata)
