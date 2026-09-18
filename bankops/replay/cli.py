import argparse
import asyncio
from pathlib import Path

from playwright.async_api import Page, async_playwright

from bankops.artifacts.models import CapabilityArtifact, ValueType
from bankops.logging.replay import JsonlEventSink, ReplayEventRecorder
from bankops.replay.engine import ReplayEngine
from bankops.replay.evidence import create_replay_evidence
from bankops.replay.models import ReplayResult, ReplayStatus, ReplayValue
from bankops.surfaces.playwright import PlaywrightSurfaceAdapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a saved BankOps capability")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Capability input; repeat for multiple values",
    )
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--failure-screenshot", type=Path)
    parser.add_argument("--headed", action="store_true")
    return parser


def parse_inputs(artifact: CapabilityArtifact, raw_inputs: list[str]) -> dict[str, ReplayValue]:
    declarations = {parameter.name: parameter for parameter in artifact.inputs}
    parsed: dict[str, ReplayValue] = {}
    for item in raw_inputs:
        name, separator, raw_value = item.partition("=")
        if not separator or not name:
            raise ValueError(f"Input must use NAME=VALUE syntax: {item!r}")
        if name in parsed:
            raise ValueError(f"Input was supplied more than once: {name}")
        declaration = declarations.get(name)
        if declaration is None:
            raise ValueError(f"Unknown input: {name}")
        parsed[name] = _parse_value(raw_value, declaration.value_type)
    return parsed


def _parse_value(raw_value: str, value_type: ValueType) -> ReplayValue:
    if value_type is ValueType.STRING:
        return raw_value
    if value_type is ValueType.INTEGER:
        return int(raw_value)
    if value_type is ValueType.NUMBER:
        return float(raw_value)
    if value_type is ValueType.BOOLEAN:
        normalized = raw_value.casefold()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        raise ValueError("Boolean inputs must be 'true' or 'false'")
    raise ValueError(f"Unsupported input type: {value_type}")


async def run(args: argparse.Namespace) -> int:
    artifact = CapabilityArtifact.model_validate_json(args.artifact.read_text())
    inputs = parse_inputs(artifact, args.input)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        recorder = ReplayEventRecorder(JsonlEventSink(args.log)) if args.log is not None else None
        result = await ReplayEngine(PlaywrightSurfaceAdapter(page), recorder=recorder).replay(
            artifact, inputs
        )
        await capture_failure_screenshot(page, args.failure_screenshot, result)
        await browser.close()

    print(result.model_dump_json(indent=2))
    if args.evidence is not None:
        evidence = create_replay_evidence(artifact, inputs, result)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(evidence.model_dump_json(indent=2) + "\n")
    return 0 if result.status in {"success", "business_outcome"} else 1


async def capture_failure_screenshot(
    page: Page,
    path: Path | None,
    result: ReplayResult,
) -> bool:
    if result.status is not ReplayStatus.FAILURE or path is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=path, full_page=True)
    return True


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
