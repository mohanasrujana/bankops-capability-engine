import pytest
from pydantic import ValidationError

from bankops.artifacts.models import LocatorPlan


def test_locator_plan_parses_ordered_candidates_by_discriminator() -> None:
    plan = LocatorPlan.model_validate(
        {
            "candidates": [
                {
                    "kind": "role",
                    "role": "button",
                    "name": "Search",
                },
                {
                    "kind": "css",
                    "selector": "form.member-search button",
                },
                {
                    "kind": "coordinate",
                    "x": 420,
                    "y": 315,
                    "viewport_width": 1280,
                    "viewport_height": 720,
                },
            ]
        }
    )

    assert [candidate.kind for candidate in plan.candidates] == [
        "role",
        "css",
        "coordinate",
    ]


def test_locator_plan_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LocatorPlan.model_validate(
            {
                "candidates": [
                    {
                        "kind": "label",
                        "label": "Member ID",
                        "invented_field": "unsafe",
                    }
                ]
            }
        )


def test_locator_plan_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        LocatorPlan(candidates=())


def test_coordinate_locator_must_be_final_fallback() -> None:
    with pytest.raises(ValidationError, match="final fallback"):
        LocatorPlan.model_validate(
            {
                "candidates": [
                    {
                        "kind": "coordinate",
                        "x": 420,
                        "y": 315,
                        "viewport_width": 1280,
                        "viewport_height": 720,
                    },
                    {
                        "kind": "text",
                        "text": "Search",
                    },
                ]
            }
        )


def test_locator_plan_allows_only_one_coordinate_fallback() -> None:
    with pytest.raises(ValidationError, match="at most one"):
        LocatorPlan.model_validate(
            {
                "candidates": [
                    {
                        "kind": "coordinate",
                        "x": 100,
                        "y": 100,
                        "viewport_width": 1280,
                        "viewport_height": 720,
                    },
                    {
                        "kind": "coordinate",
                        "x": 200,
                        "y": 200,
                        "viewport_width": 1280,
                        "viewport_height": 720,
                    },
                ]
            }
        )
