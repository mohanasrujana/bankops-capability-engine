from collections.abc import AsyncIterator

import pytest
from playwright.async_api import Page, async_playwright

from bankops.discovery.observation import PlaywrightObservationCollector
from bankops.surfaces.base import SurfaceError
from bankops.surfaces.playwright import PlaywrightSurfaceAdapter


@pytest.fixture
async def observation_page() -> AsyncIterator[Page]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            await page.route(
                "http://ledgerdesk.test/**",
                lambda route: route.fulfill(
                    body="<html><body></body></html>", content_type="text/html"
                ),
            )
            await page.goto("http://ledgerdesk.test/")
            yield page
        finally:
            await browser.close()


@pytest.mark.anyio
async def test_observation_reads_rendered_text_without_input_values(
    observation_page: Page,
) -> None:
    await observation_page.set_content(
        '<title>LedgerDesk</title><label for="member">Member ID</label>'
        '<input id="member" value="M-10001"><button>Search</button>'
        '<div hidden>hidden sentinel</div><script>const secret = "script sentinel";</script>'
        '<style>.hidden { display: none; }</style><div class="hidden">css sentinel</div>'
    )
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert str(result.url) == "http://ledgerdesk.test/"
    assert result.title == "LedgerDesk"
    assert "Member ID" in result.visible_text
    assert "Search" in result.visible_text
    assert "sentinel" not in result.visible_text
    assert "M-10001" not in result.visible_text
    assert not result.truncated
    assert await observation_page.locator("#member").input_value() == "M-10001"


@pytest.mark.anyio
@pytest.mark.parametrize(("title_size", "text_size"), [(501, 3), (3, 20_001), (500, 20_000)])
async def test_observation_bounds_unicode_and_reports_truncation(
    observation_page: Page,
    title_size: int,
    text_size: int,
) -> None:
    await observation_page.set_content(
        f"<title>{'🪙' * title_size}</title><body>{'🪙' * text_size}</body>"
    )
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert result.title == "🪙" * min(title_size, 500)
    assert result.visible_text == "🪙" * min(text_size, 20_000)
    assert result.truncated == (title_size > 500 or text_size > 20_000)


@pytest.mark.anyio
@pytest.mark.parametrize("body", ["", '<body style="display:none">hidden sentinel</body>'])
async def test_observation_represents_empty_or_hidden_page(
    observation_page: Page,
    body: str,
) -> None:
    await observation_page.set_content(body)
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert result.visible_text == ""
    assert not result.truncated


@pytest.mark.anyio
async def test_closed_page_returns_surface_error(observation_page: Page) -> None:
    collector = PlaywrightObservationCollector(observation_page)
    await observation_page.close()
    with pytest.raises(SurfaceError, match="^Unable to collect discovery observation$"):
        await collector.observe()


@pytest.mark.anyio
async def test_non_http_page_returns_surface_error(observation_page: Page) -> None:
    await observation_page.goto("about:blank")
    with pytest.raises(SurfaceError, match="^Unable to collect discovery observation$"):
        await PlaywrightObservationCollector(observation_page).observe()


@pytest.mark.anyio
async def test_control_metadata_and_observed_locators_work(observation_page: Page) -> None:
    await observation_page.set_content(
        '<label for="member">Member ID</label><input id="member" value="private sentinel">'
        '<textarea aria-label="Notes" readonly>private notes</textarea>'
        '<select aria-label="Account"><option>Savings</option></select>'
        "<button onclick=\"document.title='searched'\">Search</button>"
        '<a href="/members">Open Member</a>'
        '<input type="password" aria-label="Password" value="secret sentinel">'
        '<input type="hidden" value="hidden sentinel">'
        '<button hidden>Hidden</button><button style="visibility:hidden">Invisible</button>'
        '<fieldset disabled><input aria-label="Disabled field"></fieldset>'
        '<div aria-disabled="true"><button>Disabled button</button></div>'
    )
    result = await PlaywrightObservationCollector(observation_page).observe()
    controls = {control.name_hint: control for control in result.controls}
    assert set(controls) == {
        "Member ID",
        "Notes",
        "Account",
        "Search",
        "Open Member",
        "Password",
        "Disabled field",
        "Disabled button",
    }
    assert controls["Notes"].readonly
    assert controls["Disabled field"].disabled
    assert controls["Disabled button"].disabled
    assert controls["Password"].input_type == "password"
    assert not controls["Member ID"].disabled
    assert all("sentinel" not in control.model_dump_json() for control in result.controls)
    for control in result.controls:
        candidate = control.target.candidates[0]
        assert candidate.kind == "css"
        assert await observation_page.locator(candidate.selector).count() == 1

    adapter = PlaywrightSurfaceAdapter(observation_page)
    await adapter.fill(controls["Member ID"].target, "M-10001", 500)
    await adapter.click(controls["Search"].target, 500)
    assert await observation_page.locator("#member").input_value() == "M-10001"
    assert await observation_page.title() == "searched"


@pytest.mark.anyio
async def test_duplicate_names_have_distinct_targets(observation_page: Page) -> None:
    await observation_page.set_content(
        "<button>Open</button><div><button onclick=\"document.title='second'\">Open</button></div>"
    )
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert [control.name_hint for control in result.controls] == ["Open", "Open"]
    assert result.controls[0].target != result.controls[1].target
    await PlaywrightSurfaceAdapter(observation_page).click(result.controls[1].target, 500)
    assert await observation_page.title() == "second"


@pytest.mark.anyio
@pytest.mark.parametrize("count", [100, 101])
async def test_control_count_is_bounded(observation_page: Page, count: int) -> None:
    await observation_page.set_content("<button>Go</button>" * count)
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert len(result.controls) == min(count, 100)
    assert result.truncated == (count > 100)


@pytest.mark.anyio
async def test_control_label_references_and_unicode_limit(observation_page: Page) -> None:
    await observation_page.set_content(
        '<span id="first">Member</span><span id="second">ID</span>'
        '<input aria-labelledby="first second" aria-label="Other">'
        f'<input aria-label="{"🪙" * 501}">'
    )
    result = await PlaywrightObservationCollector(observation_page).observe()
    assert result.controls[0].name_hint == "Member ID"
    assert result.controls[1].name_hint == "🪙" * 500
    assert result.truncated
