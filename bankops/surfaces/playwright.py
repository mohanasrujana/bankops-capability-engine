import re
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from bankops.artifacts.models import (
    Checkpoint,
    CoordinateLocator,
    CssLocator,
    ElementCheckpoint,
    LabelLocator,
    LocatorPlan,
    RoleLocator,
    TextLocator,
    UrlCheckpoint,
)
from bankops.artifacts.models import Locator as ArtifactLocator
from bankops.surfaces.base import SurfaceError

_Result = TypeVar("_Result")


class PlaywrightSurfaceAdapter:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def navigate(self, url: str) -> None:
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
        except PlaywrightError as error:
            raise SurfaceError("Navigation failed") from error

    async def fill(self, target: LocatorPlan, value: str, timeout_ms: int) -> None:
        await self._try_locator_candidates(
            target,
            "fill",
            lambda locator: locator.fill(value, timeout=timeout_ms),
        )

    async def click(self, target: LocatorPlan, timeout_ms: int) -> None:
        errors: list[str] = []
        for candidate in target.candidates:
            if isinstance(candidate, CoordinateLocator):
                await self._click_coordinate(candidate)
                return
            try:
                await self._to_locator(candidate).click(timeout=timeout_ms)
                return
            except PlaywrightError:
                errors.append(candidate.kind)
        raise SurfaceError(f"No click locator succeeded; tried: {', '.join(errors)}")

    async def wait_for(self, target: LocatorPlan, state: str, timeout_ms: int) -> None:
        async def wait(locator: Locator) -> None:
            if state == "enabled":
                await expect(locator).to_be_enabled(timeout=timeout_ms)
            else:
                await locator.wait_for(state=cast(Any, state), timeout=timeout_ms)

        await self._try_locator_candidates(target, f"wait for {state}", wait)

    async def extract(self, target: LocatorPlan, source: str, timeout_ms: int) -> str:
        async def read(locator: Locator) -> str:
            await locator.wait_for(state="visible", timeout=timeout_ms)
            if source == "value":
                return await locator.input_value(timeout=timeout_ms)
            return await locator.inner_text(timeout=timeout_ms)

        return await self._try_locator_candidates(target, "extract", read)

    async def checkpoint_is_met(self, checkpoint: Checkpoint) -> bool:
        if isinstance(checkpoint, UrlCheckpoint):
            try:
                return re.search(checkpoint.pattern, self._page.url) is not None
            except re.error as error:
                raise SurfaceError("URL checkpoint contains an invalid pattern") from error

        for candidate in checkpoint.target.candidates:
            if isinstance(candidate, CoordinateLocator):
                continue
            locator = self._to_locator(candidate)
            try:
                if checkpoint.state == "visible" and await locator.is_visible():
                    return True
                if checkpoint.state == "hidden" and not await locator.is_visible():
                    return True
            except PlaywrightError:
                continue
        return False

    async def wait_for_checkpoint(self, checkpoint: Checkpoint) -> bool:
        try:
            if isinstance(checkpoint, UrlCheckpoint):
                try:
                    pattern = re.compile(checkpoint.pattern)
                except re.error as error:
                    raise SurfaceError("URL checkpoint contains an invalid pattern") from error
                await self._page.wait_for_url(pattern, timeout=checkpoint.timeout_ms)
                return True

            await self.wait_for(checkpoint.target, checkpoint.state, checkpoint.timeout_ms)
            return True
        except PlaywrightTimeoutError:
            return False
        except SurfaceError:
            if isinstance(checkpoint, ElementCheckpoint):
                return False
            raise

    async def _try_locator_candidates(
        self,
        plan: LocatorPlan,
        operation: str,
        action: Callable[[Locator], Awaitable[_Result]],
    ) -> _Result:
        attempted: list[str] = []
        for candidate in plan.candidates:
            attempted.append(candidate.kind)
            if isinstance(candidate, CoordinateLocator):
                continue
            try:
                return await action(self._to_locator(candidate))
            except PlaywrightError:
                continue
        raise SurfaceError(
            f"Unable to {operation}; locator candidates tried: {', '.join(attempted)}"
        )

    def _to_locator(self, candidate: ArtifactLocator) -> Locator:
        if isinstance(candidate, RoleLocator):
            # Playwright's generated role annotation is a large Literal union;
            # the artifact validates the runtime string at its own boundary.
            return self._page.get_by_role(
                cast(Any, candidate.role), name=candidate.name, exact=candidate.exact
            )
        if isinstance(candidate, LabelLocator):
            return self._page.get_by_label(candidate.label, exact=candidate.exact)
        if isinstance(candidate, TextLocator):
            return self._page.get_by_text(candidate.text, exact=candidate.exact)
        if isinstance(candidate, CssLocator):
            return self._page.locator(candidate.selector)
        raise SurfaceError("Coordinate locators do not identify DOM elements")

    async def _click_coordinate(self, candidate: CoordinateLocator) -> None:
        viewport = self._page.viewport_size
        if (
            viewport is None
            or viewport["width"] != candidate.viewport_width
            or viewport["height"] != candidate.viewport_height
        ):
            raise SurfaceError("Coordinate fallback viewport does not match")
        if candidate.x >= candidate.viewport_width or candidate.y >= candidate.viewport_height:
            raise SurfaceError("Coordinate fallback lies outside the viewport")
        await self._page.mouse.click(candidate.x, candidate.y)
