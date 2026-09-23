from typing import Annotated

from pydantic import Field, HttpUrl, StringConstraints

from bankops.artifacts.models import StrictModel


class DiscoveryRequest(StrictModel):
    """Validated discovery input; the execution loop must enforce policy and limits."""

    goal: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    target_url: HttpUrl
    inputs: dict[str, str] = Field(default_factory=dict)
    max_steps: int = Field(default=15, ge=1, le=50, strict=True)
    timeout_seconds: int = Field(default=120, ge=1, le=300, strict=True)
