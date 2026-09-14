from fastapi.testclient import TestClient

from ledgerdesk.app import create_app


def test_health_endpoint_reports_ledgerdesk_ready() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application": "LedgerDesk",
    }


def test_member_search_page_renders_search_form() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>LedgerDesk — Member Services</title>" in response.text
    assert 'action="/members/search"' in response.text
    assert 'name="member_id"' in response.text
    assert ">Search</button>" in response.text
    assert 'method="post"' in response.text


def test_member_search_returns_link_for_known_member() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/members/search",
        data={"member_id": "M-10001"},
    )

    assert response.status_code == 200
    assert "<h2>Member Found</h2>" in response.text
    assert 'href="/members/rec-a7f3c2"' in response.text
    assert 'href="/members/M-10001"' not in response.text
    assert ">Open Member</a>" in response.text
    assert "Savings Balance" not in response.text


def test_member_search_treats_unknown_member_as_business_outcome() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/members/search",
        data={"member_id": "M-99999"},
    )

    assert response.status_code == 200
    assert "<h2>Member Not Found</h2>" in response.text
    assert "Open Member" not in response.text


def test_member_search_rejects_invalid_identifier() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/members/search",
        data={"member_id": "10001"},
    )

    assert response.status_code == 400
    assert "<h2>Invalid Member ID</h2>" in response.text


def test_member_detail_displays_savings_balance() -> None:
    client = TestClient(create_app())

    response = client.get("/members/rec-a7f3c2")

    assert response.status_code == 200
    assert "<h2>Member Details</h2>" in response.text
    assert 'aria-label="Savings Balance"' in response.text
    assert "$4,250.75" in response.text
    assert "synthetic demonstration data" in response.text


def test_unknown_member_record_returns_safe_not_found_page() -> None:
    client = TestClient(create_app())

    response = client.get("/members/rec-unknown")

    assert response.status_code == 404
    assert "<h2>Member Record Not Found</h2>" in response.text
    assert "rec-unknown" not in response.text
