#!/usr/bin/env python3
"""Validate gate-based progress bars and project milestones in PROJECT_PLAN."""

import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
BAR_CHARACTERS = {"█", "▒", "░"}


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _phase_sections(text):
    matches = list(re.finditer(r"^## Phase (\d+): .+$", text, re.MULTILINE))
    result = {}
    for index, match in enumerate(matches):
        phase = int(match.group(1))
        finish = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[phase] = text[match.start():finish]
    return result


def _gate_count(phase, section):
    heading = (
        "### Release-candidate gate"
        if phase == 11
        else "### Exit gate"
    )
    start = section.find(heading)
    if start < 0:
        raise AssertionError(
            "Phase {} is missing {!r}".format(phase, heading)
        )
    body = section[start + len(heading):]
    next_heading = re.search(r"^#{2,3} ", body, re.MULTILINE)
    if next_heading is not None:
        body = body[:next_heading.start()]
    count = len(re.findall(r"^- ", body, re.MULTILINE))
    if count <= 0:
        raise AssertionError("Phase {} has no exit conditions".format(phase))
    return count


def _roadmap_rows(text):
    result = {}
    for line in text.splitlines():
        cells = _table_cells(line) if line.startswith("|") else []
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        progress = re.fullmatch(
            r"`([█▒░]+)` — (\d+)/(\d+)(?: .*)?", cells[2]
        )
        if progress is None:
            continue
        result[int(cells[0])] = {
            "bar": progress.group(1),
            "evidenced": int(progress.group(2)),
            "total": int(progress.group(3)),
            "state": cells[3],
        }
    return result


def _validate_phase_bars(text):
    sections = _phase_sections(text)
    rows = _roadmap_rows(text)
    assert set(sections) == set(range(12)), "phase heading set changed"
    assert set(rows) == set(range(12)), "roadmap progress row set changed"

    for phase in range(12):
        gate_count = _gate_count(phase, sections[phase])
        row = rows[phase]
        bar = row["bar"]
        assert set(bar) <= BAR_CHARACTERS, (
            "Phase {} uses an unknown bar character".format(phase)
        )
        assert len(bar) == gate_count == row["total"], (
            "Phase {} bar/denominator does not match its {} exit conditions"
            .format(phase, gate_count)
        )
        assert bar.count("█") == row["evidenced"], (
            "Phase {} evidenced count does not match its bar".format(phase)
        )
        if row["state"].startswith("Not started"):
            assert set(bar) == {"░"} and row["evidenced"] == 0, (
                "Not-started Phase {} shows progress".format(phase)
            )
        if row["state"].startswith("Complete"):
            assert set(bar) == {"█"}, (
                "Complete Phase {} has an open bar cell".format(phase)
            )
    return rows


def _validate_gate_register(section, phase, phase_row, heading):
    start = section.index(heading)
    finish = section.index("### Goal", start)
    register = section[start:finish]
    states = []
    for line in register.splitlines():
        cells = _table_cells(line) if line.startswith("|") else []
        if len(cells) != 3 or cells[0] in {
            "Exit condition", "---"
        }:
            continue
        states.append(cells[1])
    evidenced = sum(state == "Evidenced" for state in states)
    active = sum(state.startswith("Active") for state in states)
    pending = sum(state.startswith("Pending") for state in states)
    assert len(states) == phase_row["total"], (
        "Phase {} register row count does not match its exit-gate total".format(
            phase
        )
    )
    assert evidenced == phase_row["evidenced"], (
        "Phase {} evidenced register count does not match its roadmap bar".format(
            phase
        )
    )
    assert active == phase_row["bar"].count("▒"), (
        "Phase {} active register count does not match its roadmap bar".format(phase)
    )
    assert pending == phase_row["bar"].count("░"), (
        "Phase {} pending register count does not match its roadmap bar".format(
            phase
        )
    )
    assert evidenced + active + pending == len(states), (
        "Phase {} register contains an unsupported state".format(phase)
    )


def _validate_milestones(text):
    match = re.search(r"Milestone progress: `([█▒░]+)`", text)
    assert match is not None, "milestone progress bar is missing"
    bar = match.group(1)
    states = []
    identifiers = []
    for line in text.splitlines():
        cells = _table_cells(line) if line.startswith("|") else []
        if len(cells) != 4 or not re.match(r"M\d+ — ", cells[0]):
            continue
        identifiers.append(cells[0].split(" ", 1)[0])
        states.append(cells[3])
    assert identifiers == ["M{}".format(value) for value in range(1, 10)], (
        "milestone identifiers must remain M1 through M9"
    )
    complete = sum(state.startswith("Complete") for state in states)
    active = sum(state == "Active" for state in states)
    not_started = sum(state == "Not started" for state in states)
    assert len(bar) == len(states), "milestone bar length drifted"
    assert bar.count("█") == complete, "milestone complete count drifted"
    assert bar.count("▒") == active, "milestone active count drifted"
    assert bar.count("░") == not_started, (
        "milestone not-started count drifted"
    )
    assert complete + active + not_started == len(states), (
        "milestone table contains an unsupported state"
    )


def main():
    text = PLAN_PATH.read_text(encoding="utf-8")
    sections = _phase_sections(text)
    rows = _validate_phase_bars(text)
    current = [phase for phase, row in rows.items() if row["state"] == "Current"]
    assert current == [3], "Phase 3 must be the sole current phase"
    _validate_gate_register(
        sections[1], 1, rows[1], "### Final gate register"
    )
    _validate_gate_register(
        sections[current[0]],
        current[0],
        rows[current[0]],
        "### Current gate register",
    )
    _validate_milestones(text)
    print("Project plan progress validation passed")


if __name__ == "__main__":
    main()
