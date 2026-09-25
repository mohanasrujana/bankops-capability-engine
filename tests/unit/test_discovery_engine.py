import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bankops.artifacts.models import OutcomeDefinition, UrlCheckpoint
from bankops.discovery.engine import (
    ActionAuthorizer,
    DiscoveryContract,
    DiscoveryEngine,
    ObservationCollector,
)
from bankops.discovery.models import DiscoveryObservation, DiscoveryRequest
from bankops.discovery.provider import DecisionEnvelope, DecisionProvider, DecisionProviderError
from bankops.surfaces.base import SurfaceAdapter, SurfaceError


def request(**overrides: object) -> DiscoveryRequest:
    return DiscoveryRequest.model_validate(
        {
            "goal": "Find savings balance",
            "target_url": "http://ledgerdesk.test/",
            "inputs": {"member_id": "M-10001"},
            **overrides,
        }
    )


def contract() -> DiscoveryContract:
    return DiscoveryContract.model_validate(
        {
            "policy": {
                "allowed_action_kinds": ["fill", "click", "wait_for", "extract"],
                "allowed_url_prefixes": ["http://ledgerdesk.test/"],
            },
            "output_names": ["balance"],
            "success_checkpoint": {"kind": "url", "pattern": "/member"},
        }
    )


def action(kind: str, **overrides: object) -> dict[str, object]:
    step: dict[str, object] = {
        "kind": kind,
        "id": kind.replace("_", "-"),
        "description": "Proposed action",
        "target": {"candidates": [{"kind": "css", "selector": "#control"}]},
    }
    if kind == "fill":
        step["value_template"] = "{{ inputs.member_id }}"
    if kind == "extract":
        step["output_name"] = "balance"
    step.update(overrides)
    return {"kind": "act", "action": step}


SUCCESS = {"kind": "success", "checkpoint": {"kind": "url", "pattern": "/"}}


def harness(*decisions: dict[str, object], authorized: bool = True) -> SimpleNamespace:
    observation = DiscoveryObservation.model_validate(
        {
            "url": "http://ledgerdesk.test/",
            "title": "LedgerDesk",
            "visible_text": "Member ID",
            "truncated": False,
            "controls": [
                {
                    "tag": "input",
                    "input_type": "text",
                    "name_hint": "Member ID",
                    "target": {"candidates": [{"kind": "css", "selector": "#control"}]},
                    "disabled": False,
                    "readonly": False,
                }
            ],
        }
    )
    surface = MagicMock(spec=SurfaceAdapter)
    surface.extract.return_value = "$4,250.75"
    surface.checkpoint_is_met.return_value = False
    surface.wait_for_checkpoint.return_value = True
    collector = MagicMock(spec=ObservationCollector)
    collector.observe.return_value = observation
    provider = MagicMock(spec=DecisionProvider)
    provider.decide.side_effect = [
        DecisionEnvelope.model_validate({"decision": decision}).decision for decision in decisions
    ]
    authorizer = MagicMock(spec=ActionAuthorizer)
    authorizer.authorize.return_value = authorized
    return SimpleNamespace(
        engine=DiscoveryEngine(surface, collector, provider, authorizer=authorizer),
        surface=surface,
        collector=collector,
        provider=provider,
        authorizer=authorizer,
        observation=observation,
    )


@pytest.mark.anyio
async def test_loop_binds_inputs_records_steps_and_verifies_trusted_success() -> None:
    h = harness(action("fill"), action("click"), action("wait_for"), action("extract"), SUCCESS)
    result = await h.engine.discover(request(), contract())
    assert result.status == "success"
    assert result.outputs == {"balance": "$4,250.75"}
    assert [step.kind for step in result.completed_steps] == [
        "fill",
        "click",
        "wait_for",
        "extract",
    ]
    assert result.decision_count == 5
    assert h.surface.fill.await_args.args[1] == "M-10001"
    assert h.surface.wait_for_checkpoint.await_args_list[0].args[0] == contract().success_checkpoint
    assert h.authorizer.authorize.await_count == 4
    context = h.provider.decide.await_args.args[0]
    assert context.output_names == ("balance",)
    assert context.expected_output_names == ("balance",)
    assert context.completed_steps[0].value_template == "{{ inputs.member_id }}"


@pytest.mark.anyio
@pytest.mark.parametrize("authorized", [False, None])
async def test_even_model_labeled_safe_actions_require_authorization(
    authorized: bool | None,
) -> None:
    h = harness(action("fill", risk="safe"), authorized=False)
    if authorized is None:
        h.engine = DiscoveryEngine(h.surface, h.collector, h.provider)
    result = await h.engine.discover(request(), contract())
    assert result.status == "intervention_required"
    assert result.code == "action_not_authorized"
    h.surface.fill.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("decision", "code"),
    [
        (action("fill", risk="irreversible"), "irreversible_action"),
        (action("fill", value_template="M-10001"), "invalid_input_reference"),
        (action("fill", value_template="{{ inputs.unknown }}"), "invalid_input_reference"),
        (action("extract", output_name="unexpected"), "invalid_output_name"),
        (
            action("wait_for", retry={"max_attempts": 2, "delay_ms": 0}),
            "discovery_retry_not_supported",
        ),
    ],
)
async def test_invalid_proposals_stop_before_authorization(
    decision: dict[str, object], code: str
) -> None:
    h = harness(decision)
    result = await h.engine.discover(request(), contract())
    assert result.status == "failure"
    assert result.code == code
    h.authorizer.authorize.assert_not_awaited()


@pytest.mark.anyio
async def test_action_allowlist_is_enforced() -> None:
    h = harness(action("click"))
    criteria = contract()
    criteria = criteria.model_copy(
        update={
            "policy": criteria.policy.model_copy(
                update={"allowed_action_kinds": frozenset({"extract"})}
            )
        }
    )
    result = await h.engine.discover(request(), criteria)
    assert result.code == "action_not_allowed"
    h.surface.click.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize("changed", ["disabled", "readonly", "password", "missing"])
async def test_fill_requires_current_actionable_control(changed: str) -> None:
    h = harness(action("fill"))
    data = h.observation.model_dump(mode="json")
    if changed == "missing":
        data["controls"] = []
    elif changed == "password":
        data["controls"][0]["input_type"] = "password"
    else:
        data["controls"][0][changed] = True
    h.collector.observe.return_value = DiscoveryObservation.model_validate(data)
    result = await h.engine.discover(request(), contract())
    assert result.code == "control_not_actionable"
    h.surface.fill.assert_not_awaited()


@pytest.mark.anyio
async def test_authorization_state_change_stops_before_action() -> None:
    h = harness(action("fill"))
    h.collector.observe.side_effect = [
        h.observation,
        h.observation,
        h.observation.model_copy(update={"visible_text": "Different form"}),
    ]
    result = await h.engine.discover(request(), contract())
    assert result.code == "state_changed_during_authorization"
    h.surface.fill.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize("url", ["http://ledgerdesk.test.evil/", "https://ledgerdesk.test/"])
async def test_initial_target_rejection_precedes_navigation(url: str) -> None:
    h = harness()
    result = await h.engine.discover(request(target_url=url), contract())
    assert result.code == "target_not_allowed"
    h.surface.navigate.assert_not_awaited()


@pytest.mark.anyio
async def test_redirect_stops_before_model_receives_outside_page() -> None:
    h = harness()
    h.collector.observe.return_value = DiscoveryObservation.model_validate(
        {
            **h.observation.model_dump(mode="json"),
            "url": "http://outside.test/",
        }
    )
    result = await h.engine.discover(request(), contract())
    assert result.code == "target_not_allowed"
    h.provider.decide.assert_not_awaited()


@pytest.mark.anyio
async def test_model_cannot_claim_success_without_outputs() -> None:
    h = harness(SUCCESS)
    result = await h.engine.discover(request(), contract())
    assert result.code == "missing_outputs"


@pytest.mark.anyio
async def test_trusted_checkpoint_cannot_be_replaced_by_model_checkpoint() -> None:
    h = harness(action("extract"), SUCCESS)
    h.surface.wait_for_checkpoint.return_value = False
    result = await h.engine.discover(request(), contract())
    assert result.code == "trusted_checkpoint_not_met"
    assert h.surface.wait_for_checkpoint.await_args.args[0] == contract().success_checkpoint


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("second", "code"),
    [
        (action("extract"), "duplicate_step_id"),
        (action("extract", id="extract-again"), "invalid_output_name"),
    ],
)
async def test_completed_steps_and_outputs_cannot_be_overwritten(
    second: dict[str, object], code: str
) -> None:
    h = harness(action("extract"), second)
    result = await h.engine.discover(request(), contract())
    assert result.code == code
    assert h.surface.extract.await_count == 1


@pytest.mark.anyio
async def test_decision_budget_stops_without_extra_model_call() -> None:
    h = harness(action("wait_for"))
    result = await h.engine.discover(request(max_steps=1), contract())
    assert result.status == "max_steps"
    assert result.decision_count == 1
    assert len(result.completed_steps) == 1
    assert h.provider.decide.await_count == 1


@pytest.mark.anyio
@pytest.mark.parametrize("phase", ["provider", "surface"])
async def test_total_deadline_covers_provider_and_action(phase: str) -> None:
    h = harness(action("fill"))

    async def hang(*args: object) -> None:
        await asyncio.sleep(10)

    if phase == "provider":
        h.provider.decide.side_effect = hang
    else:
        h.surface.fill.side_effect = hang
    result = await h.engine.discover(request(timeout_seconds=1), contract())
    assert result.status == "timeout"
    assert result.completed_steps == ()


@pytest.mark.anyio
async def test_external_cancellation_propagates() -> None:
    h = harness()
    h.provider.decide.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await h.engine.discover(request(), contract())


@pytest.mark.anyio
@pytest.mark.parametrize("reason", ["dead_end", "intervention_required", "business_outcome"])
async def test_model_stop_reasons_do_not_invent_verified_outcomes(reason: str) -> None:
    h = harness({"kind": "stop", "reason": reason, "message": "private sentinel"})
    result = await h.engine.discover(request(), contract())
    assert result.status == ("failure" if reason == "business_outcome" else reason)
    assert "private sentinel" not in result.model_dump_json()


@pytest.mark.anyio
async def test_trusted_business_outcome_stops_before_model_call() -> None:
    h = harness()
    criteria = contract().model_copy(
        update={
            "outcomes": (
                OutcomeDefinition(
                    code="member_not_found",
                    description="Missing member",
                    checkpoint=UrlCheckpoint(pattern="/missing"),
                ),
            )
        }
    )
    h.surface.checkpoint_is_met.return_value = True
    result = await h.engine.discover(request(), criteria)
    assert result.status == "business_outcome"
    assert result.code == "member_not_found"
    h.provider.decide.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize("phase", ["provider", "surface"])
async def test_failures_are_sanitized_and_not_retried(phase: str) -> None:
    h = harness(action("fill"))
    if phase == "provider":
        h.provider.decide.side_effect = DecisionProviderError("private sentinel")
    else:
        h.surface.fill.side_effect = SurfaceError("private sentinel")
    result = await h.engine.discover(request(), contract())
    assert result.code == f"{phase}_error"
    assert "private sentinel" not in result.model_dump_json()
    assert h.provider.decide.await_count == 1
    assert h.surface.fill.await_count == (1 if phase == "surface" else 0)
