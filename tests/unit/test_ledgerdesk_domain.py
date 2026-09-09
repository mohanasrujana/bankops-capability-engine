from ledgerdesk.domain import (
    FoundResult,
    InvalidInputResult,
    NotFoundResult,
    lookup_member,
)


def test_lookup_returns_known_synthetic_member() -> None:
    result = lookup_member("M-10001")

    assert isinstance(result, FoundResult)
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
