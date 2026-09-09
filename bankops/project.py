from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    name: str
    target_application: str


PROJECT = ProjectIdentity(
    name="BankOps Capability Engine",
    target_application="LedgerDesk",
)


def describe_project() -> str:
    return f"{PROJECT.name} automates {PROJECT.target_application}."
