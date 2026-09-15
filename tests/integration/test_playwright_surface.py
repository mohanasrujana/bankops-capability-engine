import pytest
from playwright.async_api import async_playwright

from bankops.artifacts.models import (
    ElementCheckpoint,
    LocatorPlan,
    UrlCheckpoint,
)
from bankops.surfaces.base import SurfaceError
from bankops.surfaces.playwright import PlaywrightSurfaceAdapter


@pytest.mark.anyio
async def test_adapter_uses_ordered_fallback_for_fill_and_extract() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.set_content(
            '<label for="member">Member ID</label><input id="member">'
            '<output aria-label="Savings Balance">$4,250.75</output>'
        )
        adapter = PlaywrightSurfaceAdapter(page)

        await adapter.fill(
            LocatorPlan.model_validate(
                {
                    "candidates": [
                        {"kind": "label", "label": "Wrong Label"},
                        {"kind": "css", "selector": "#member"},
                    ]
                }
            ),
            "M-10001",
            100,
        )
        extracted = await adapter.extract(
            LocatorPlan.model_validate(
                {"candidates": [{"kind": "label", "label": "Savings Balance"}]}
            ),
            "text",
            100,
        )

        assert await page.locator("#member").input_value() == "M-10001"
        assert extracted == "$4,250.75"
        await browser.close()


@pytest.mark.anyio
async def test_adapter_clicks_by_accessible_role() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.set_content("<button onclick=\"this.textContent='Done'\">Search</button>")
        adapter = PlaywrightSurfaceAdapter(page)

        await adapter.click(
            LocatorPlan.model_validate(
                {"candidates": [{"kind": "role", "role": "button", "name": "Search"}]}
            ),
            500,
        )

        assert await page.get_by_role("button").inner_text() == "Done"
        await browser.close()


@pytest.mark.anyio
async def test_adapter_checks_element_and_url_checkpoints() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.set_content("<h2>Member Found</h2>")
        adapter = PlaywrightSurfaceAdapter(page)
        element = ElementCheckpoint.model_validate(
            {
                "target": {
                    "candidates": [{"kind": "role", "role": "heading", "name": "Member Found"}]
                }
            }
        )
        url = UrlCheckpoint(pattern=r"^about:blank$")

        assert await adapter.checkpoint_is_met(element) is True
        assert await adapter.checkpoint_is_met(url) is True
        assert await adapter.wait_for_checkpoint(element) is True
        await browser.close()


@pytest.mark.anyio
async def test_coordinate_click_rejects_viewport_mismatch() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 800, "height": 600})
        adapter = PlaywrightSurfaceAdapter(page)
        plan = LocatorPlan.model_validate(
            {
                "candidates": [
                    {
                        "kind": "coordinate",
                        "x": 10,
                        "y": 10,
                        "viewport_width": 1024,
                        "viewport_height": 768,
                    }
                ]
            }
        )

        with pytest.raises(SurfaceError, match="viewport does not match"):
            await adapter.click(plan, 100)
        await browser.close()


@pytest.mark.anyio
async def test_missing_element_checkpoint_returns_false() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.set_content("<h2>Still Loading</h2>")
        adapter = PlaywrightSurfaceAdapter(page)
        checkpoint = ElementCheckpoint.model_validate(
            {
                "target": {"candidates": [{"kind": "role", "role": "heading", "name": "Complete"}]},
                "timeout_ms": 100,
            }
        )

        assert await adapter.wait_for_checkpoint(checkpoint) is False
        await browser.close()
