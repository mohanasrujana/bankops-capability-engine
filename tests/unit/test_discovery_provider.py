import json
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
from openai import AsyncOpenAI

from bankops.discovery.provider import (
    DecisionContext,
    DecisionProviderError,
    OpenAIDecisionProvider,
    decision_schema,
)


def context() -> DecisionContext:
    return DecisionContext.model_validate(
        {
            "request": {
                "goal": "Find the savings balance",
                "target_url": "http://ledgerdesk.test",
                "inputs": {"member_id": "private-input-sentinel"},
            },
            "observation": {
                "url": "http://ledgerdesk.test",
                "title": "LedgerDesk",
                "visible_text": "Member ID Search",
                "truncated": False,
            },
        }
    )


def response_body(text: str, *, status: str = "completed", refusal: bool = False) -> dict[str, Any]:
    content = (
        {"type": "refusal", "refusal": "private-refusal-sentinel"}
        if refusal
        else {"type": "output_text", "text": text, "annotations": [], "logprobs": []}
    )
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 0,
        "model": "test-model",
        "status": status,
        "output": [
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [content],
            }
        ],
    }


@pytest.mark.anyio
async def test_sdk_sends_schema_and_parses_decision_without_input_values() -> None:
    requests: list[httpx2.Request] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            200,
            json=response_body(
                json.dumps(
                    {"decision": {"kind": "stop", "reason": "dead_end", "message": "No controls"}}
                )
            ),
        )

    async with (
        httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http_client,
        AsyncOpenAI(api_key="test-key", http_client=http_client) as client,
    ):
        result = await OpenAIDecisionProvider(client, model="test-model").decide(context())

    assert result.kind == "stop"
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["model"] == "test-model"
    assert body["store"] is False
    assert body["max_output_tokens"] == 4096
    assert body["text"]["format"]["strict"] is True
    assert body["text"]["format"]["schema"] == decision_schema()
    assert "private-input-sentinel" not in body["input"]
    payload = json.loads(body["input"])
    assert payload["input_names"] == ["member_id"]
    assert payload["observation"]["visible_text"] == "Member ID Search"
    assert "untrusted data" in body["instructions"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("text", "status", "refusal", "message"),
    [
        ("private-response-sentinel", "completed", False, "decision contract"),
        ('{"decision":{"kind":"execute_shell"}}', "completed", False, "decision contract"),
        ("", "incomplete", False, "not completed"),
        ("", "completed", True, "declined"),
        ("", "completed", False, "decision contract"),
    ],
)
async def test_provider_rejects_unusable_responses(
    text: str,
    status: str,
    refusal: bool,
    message: str,
) -> None:
    def respond(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=response_body(text, status=status, refusal=refusal))

    async with (
        httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http_client,
        AsyncOpenAI(api_key="test-key", http_client=http_client) as client,
    ):
        with pytest.raises(DecisionProviderError, match=message) as error:
            await OpenAIDecisionProvider(client, model="test-model").decide(context())
    assert "sentinel" not in str(error.value)


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["server", "timeout"])
async def test_provider_does_not_retry_failed_requests(failure: str) -> None:
    calls = 0

    def respond(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        if failure == "timeout":
            raise httpx2.ReadTimeout("private-error-sentinel", request=request)
        return httpx2.Response(500, json={"error": {"message": "private-error-sentinel"}})

    async with (
        httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http_client,
        AsyncOpenAI(api_key="test-key", http_client=http_client) as client,
    ):
        with pytest.raises(DecisionProviderError, match="^Model request failed$"):
            await OpenAIDecisionProvider(client, model="test-model").decide(context())
    assert calls == 1


def test_wire_schema_uses_required_closed_objects_and_anyof() -> None:
    def nodes(value: Any) -> Iterator[dict[str, Any]]:
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from nodes(child)
        elif isinstance(value, list):
            for child in value:
                yield from nodes(child)

    schema = decision_schema()
    assert schema["type"] == "object"
    assert "anyOf" not in schema
    for node in nodes(schema):
        assert not {"discriminator", "oneOf", "default", "const"} & node.keys()
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
    assert "anyOf" in schema["$defs"]["DiscoveryDecision"]
