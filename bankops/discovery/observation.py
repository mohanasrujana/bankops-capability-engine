import asyncio

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from pydantic import ValidationError

from bankops.discovery.models import DiscoveryObservation
from bankops.surfaces.base import SurfaceError


class PlaywrightObservationCollector:
    """Read bounded main-document text without navigating or changing the page."""

    def __init__(self, page: Page) -> None:
        self._page = page

    async def observe(self) -> DiscoveryObservation:
        try:
            async with asyncio.timeout(5):
                snapshot = await self._page.evaluate(
                    """() => {
                        const title = Array.from(document.title);
                        const body = document.body;
                        // innerText on a non-rendered root can fall back to textContent.
                        const text = Array.from(body && body.checkVisibility()
                            ? body.innerText : '');
                        return {
                            url: window.location.href,
                            title: title.slice(0, 500).join(''),
                            visible_text: text.slice(0, 20000).join(''),
                            truncated: title.length > 500 || text.length > 20000,
                        };
                    }"""
                )
                return DiscoveryObservation.model_validate(snapshot)
        except (PlaywrightError, ValidationError, TimeoutError) as error:
            # Browser errors and validation details can include raw page data.
            raise SurfaceError("Unable to collect discovery observation") from error
