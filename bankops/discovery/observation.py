import asyncio

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from pydantic import ValidationError

from bankops.discovery.models import DiscoveryObservation
from bankops.surfaces.base import SurfaceError


class PlaywrightObservationCollector:
    """Read bounded main-document text and native controls without changing the page."""

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
                        let truncated = title.length > 500 || text.length > 20000;
                        const controls = [];
                        for (const element of document.querySelectorAll(
                            'input, textarea, select, button, a[href]'
                        )) {
                            if (!element.checkVisibility({visibilityProperty: true}) ||
                                element.getClientRects().length === 0) continue;
                            if (controls.length === 100) {
                                truncated = true;
                                break;
                            }
                            // A structural selector is exact for this snapshot and
                            // avoids assuming that a label is unique or accessible.
                            const parts = [];
                            for (let node = element; node; node = node.parentElement) {
                                let index = 1;
                                for (let sibling = node.previousElementSibling; sibling;
                                     sibling = sibling.previousElementSibling) {
                                    if (sibling.localName === node.localName) index++;
                                }
                                parts.unshift(`${node.localName}:nth-of-type(${index})`);
                            }
                            const selector = parts.join(' > ');
                            if (selector.length > 4096) {
                                truncated = true;
                                continue;
                            }
                            const labelledBy = (element.getAttribute('aria-labelledby') || '')
                                .split(/\\s+/).filter(Boolean)
                                .map(id => document.getElementById(id)?.textContent || '')
                                .join(' ').trim();
                            const labels = Array.from(element.labels || [])
                                .map(label => label.innerText).join(' ').trim();
                            const hint = labelledBy || element.getAttribute('aria-label') ||
                                labels || (['button', 'a'].includes(element.localName)
                                    ? element.innerText : '') ||
                                element.getAttribute('placeholder') || '';
                            const name = Array.from(hint.trim());
                            if (name.length > 500) truncated = true;
                            controls.push({
                                tag: element.localName,
                                input_type: element.localName === 'input' ? element.type : null,
                                name_hint: name.slice(0, 500).join(''),
                                target: {candidates: [{kind: 'css', selector}]},
                                disabled: element.matches(':disabled') ||
                                    element.closest('[aria-disabled="true"], [inert]') !== null,
                                readonly: element.matches('[readonly]') ||
                                    element.getAttribute('aria-readonly') === 'true',
                            });
                        }
                        return {
                            url: window.location.href,
                            title: title.slice(0, 500).join(''),
                            visible_text: text.slice(0, 20000).join(''),
                            truncated,
                            controls,
                        };
                    }"""
                )
                return DiscoveryObservation.model_validate(snapshot)
        except (PlaywrightError, ValidationError, TimeoutError) as error:
            # Browser errors and validation details can include raw page data.
            raise SurfaceError("Unable to collect discovery observation") from error
