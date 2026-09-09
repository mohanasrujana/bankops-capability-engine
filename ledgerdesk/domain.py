from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class MemberIdInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    member_id: str = Field(pattern=r"^M-\d{5}$")


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    display_name: str
    savings_balance_cents: int = Field(ge=0)


class FoundResult(BaseModel):
    status: Literal["found"] = "found"
    member: Member


class NotFoundResult(BaseModel):
    status: Literal["not_found"] = "not_found"
    member_id: str


class InvalidInputResult(BaseModel):
    status: Literal["invalid_input"] = "invalid_input"
    issues: tuple[str, ...]


type LookupResult = FoundResult | NotFoundResult | InvalidInputResult


_MEMBERS: dict[str, Member] = {
    "M-10001": Member(
        id="M-10001",
        display_name="Synthetic Member 10001",
        savings_balance_cents=425_075,
    ),
    "M-10002": Member(
        id="M-10002",
        display_name="Synthetic Member 10002",
        savings_balance_cents=98_750,
    ),
}


def lookup_member(raw_member_id: object) -> LookupResult:
    try:
        request = MemberIdInput.model_validate({"member_id": raw_member_id})
    except ValidationError as error:
        return InvalidInputResult(
            issues=tuple(issue["msg"] for issue in error.errors()),
        )

    member = _MEMBERS.get(request.member_id)

    if member is None:
        return NotFoundResult(member_id=request.member_id)

    return FoundResult(member=member)
