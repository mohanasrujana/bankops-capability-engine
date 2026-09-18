from typing import Protocol

from bankops.artifacts.models import RiskLevel, StrictModel


class ApprovalRequest(StrictModel):
    capability_id: str
    step_id: str
    action_kind: str
    risk: RiskLevel
    description: str


class ApprovalProvider(Protocol):
    async def approve(self, request: ApprovalRequest) -> bool: ...


class DenyByDefaultApprovalProvider:
    async def approve(self, request: ApprovalRequest) -> bool:
        return False
