from extraction.edgar.tickers import _format_cik, _split_company_name_and_tag, _to_csv_row


def test_split_company_name_and_tag_strips_de_suffix():
    assert _split_company_name_and_tag("APPLIED MATERIALS INC /DE") == (
        "APPLIED MATERIALS INC",
        "DE",
    )
    assert _split_company_name_and_tag("BANK OF AMERICA CORP /DE/") == (
        "BANK OF AMERICA CORP",
        "DE",
    )
    assert _split_company_name_and_tag("QUALCOMM INC/DE") == ("QUALCOMM INC", "DE")


def test_split_company_name_and_tag_generalizes_to_any_suffix():
    assert _split_company_name_and_tag("SOME BANK PLC/ADR") == ("SOME BANK PLC", "ADR")
    assert _split_company_name_and_tag("SOME OHIO CO /OH/") == ("SOME OHIO CO", "OH")


def test_split_company_name_and_tag_handles_bare_trailing_slash():
    assert _split_company_name_and_tag("TOYOTA MOTOR CORP/") == ("TOYOTA MOTOR CORP", "")


def test_split_company_name_and_tag_leaves_plain_names_untouched():
    assert _split_company_name_and_tag("Meta Platforms, Inc.") == ("Meta Platforms, Inc.", "")
    assert _split_company_name_and_tag("Apple Inc.") == ("Apple Inc.", "")


def test_format_cik_zero_pads_to_ten_digits():
    assert _format_cik(320193) == "CIK0000320193"


def test_to_csv_row_builds_expected_fields():
    entry = {"ticker": "aapl", "cik_str": 320193, "title": "Apple Inc."}

    row = _to_csv_row(entry)

    assert row == {
        "ticker": "aapl",
        "cik_number": 320193,
        "cik_str": "CIK0000320193",
        "company_name": "Apple Inc.",
        "tags": "",
    }
