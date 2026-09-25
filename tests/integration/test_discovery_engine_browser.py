from unittest.mock import MagicMock

import pytest
from playwright.async_api import async_playwright

from bankops.discovery.engine import ActionAuthorizer, DiscoveryContract, DiscoveryEngine
from bankops.discovery.models import (
    ActionDecision,
    DiscoveryDecision,
    DiscoveryRequest,
    SuccessDecision,
)
from bankops.discovery.observation import PlaywrightObservationCollector
from bankops.discovery.provider import DecisionContext
from bankops.surfaces.playwright import PlaywrightSurfaceAdapter

_HTML = """<html><title>LedgerDesk test</title><body>
<label for="member">Member ID</label><input id="member">
<button onclick="if(document.querySelector('#member').value === 'M-10001') {
document.querySelector('#balance').hidden=false; }">Search</button>
<output id="balance" hidden>$4,250.75</output>
</body></html>"""


class ScriptedProvider:
    """Test fixture only; no model call or genuine discovery evidence."""

    async def decide(self, context: DecisionContext) -> DiscoveryDecision:
        index = len(context.completed_steps)
        if index == 0:
            control = next(c for c in context.observation.controls if c.name_hint == "Member ID")
            return ActionDecision.model_validate(
                {
                    "action": {
                        "kind": "fill",
                        "id": "enter-member",
                        "description": "Enter ID",
                        "target": control.target.model_dump(mode="json"),
                        "value_template": "{{ inputs.member_id }}",
                    }
                }
            )
        if index == 1:
            control = next(c for c in context.observation.controls if c.name_hint == "Search")
            return ActionDecision.model_validate(
                {
                    "action": {
                        "kind": "click",
                        "id": "search",
                        "description": "Search member",
                        "target": control.target.model_dump(mode="json"),
                    }
                }
            )
        if index == 2:
            return ActionDecision.model_validate(
                {
                    "action": {
                        "kind": "extract",
                        "id": "read-balance",
                        "description": "Read balance",
                        "target": {"candidates": [{"kind": "css", "selector": "#balance"}]},
                        "output_name": "balance",
                    }
                }
            )
        assert context.output_names == ("balance",)
        assert context.success_checkpoint is not None
        return SuccessDecision(checkpoint=context.success_checkpoint)


@pytest.mark.anyio
async def test_scripted_discovery_runs_against_real_chromium() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            await page.route(
                "http://ledgerdesk.test/**",
                lambda route: route.fulfill(
                    body=_HTML,
                    content_type="text/html",
                ),
            )
            authorizer = MagicMock(spec=ActionAuthorizer)
            authorizer.authorize.return_value = True
            engine = DiscoveryEngine(
                PlaywrightSurfaceAdapter(page),
                PlaywrightObservationCollector(page),
                ScriptedProvider(),
                authorizer=authorizer,
            )
            result = await engine.discover(
                DiscoveryRequest.model_validate(
                    {
                        "goal": "Find the member savings balance",
                        "target_url": "http://ledgerdesk.test/",
                        "inputs": {"member_id": "M-10001"},
                    }
                ),
                DiscoveryContract.model_validate(
                    {
                        "policy": {
                            "allowed_action_kinds": ["fill", "click", "extract"],
                            "allowed_url_prefixes": ["http://ledgerdesk.test/"],
                        },
                        "output_names": ["balance"],
                        "success_checkpoint": {
                            "kind": "element",
                            "target": {
                                "candidates": [{"kind": "css", "selector": "#balance"}],
                            },
                        },
                    }
                ),
            )
            assert result.status == "success"
            assert result.outputs == {"balance": "$4,250.75"}
            assert result.decision_count == 4
            assert [step.kind for step in result.completed_steps] == ["fill", "click", "extract"]
            assert await page.locator("#member").input_value() == "M-10001"
            assert not page.is_closed()
        finally:
            await browser.close()
