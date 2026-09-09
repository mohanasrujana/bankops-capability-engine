from bankops.project import PROJECT, describe_project


def test_project_identity_names_engine_and_target() -> None:
    assert PROJECT.name == "BankOps Capability Engine"
    assert PROJECT.target_application == "LedgerDesk"


def test_project_description_explains_relationship() -> None:
    assert describe_project() == "BankOps Capability Engine automates LedgerDesk."
