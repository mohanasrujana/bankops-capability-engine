from ledgerdesk.domain import (
    FoundResult,
    InvalidInputResult,
    NotFoundResult,
    format_usd,
    lookup_member,
    lookup_member_record,
)


def test_lookup_returns_known_synthetic_member() -> None:
    result = lookup_member("M-10001")

    assert isinstance(result, FoundResult)
    assert result.member.record_id == "rec-a7f3c2"
    assert result.member.id == "M-10001"
    assert result.member.display_name == "Synthetic Member 10001"
    assert result.member.savings_balance_cents == 425_075


def test_lookup_returns_business_outcome_for_unknown_member() -> None:
    result = lookup_member("M-99999")

    assert isinstance(result, NotFoundResult)
    assert result.member_id == "M-99999"


def test_lookup_rejects_malformed_member_id() -> None:
    result = lookup_member("10001")

    assert isinstance(result, InvalidInputResult)
    assert result.issues


def test_lookup_trims_surrounding_whitespace() -> None:
    result = lookup_member("  M-10002  ")

    assert isinstance(result, FoundResult)
    assert result.member.id == "M-10002"


def test_lookup_member_record_uses_non_member_identifier() -> None:
    member = lookup_member_record("rec-a7f3c2")

    assert member is not None
    assert member.id == "M-10001"


def test_lookup_member_record_returns_none_for_unknown_record() -> None:
    assert lookup_member_record("rec-unknown") is None


def test_format_usd_uses_integer_cents() -> None:
    assert format_usd(425_075) == "$4,250.75"
