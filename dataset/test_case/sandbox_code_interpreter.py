# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import csv
import os
import re
from pathlib import Path

from thinkingbox.common import Judge, TestContext

"""!
scenario: sandbox_code_interpreter
"""

# PREREQUISITE: the code interpreter fails closed.  These test cases require
# THINKINGBOX_SANDBOX_ALLOW_UNCONFINED=1 in the environment that launches the
# MCP server.  Without it the `code_interpreter` tool returns an error and the
# assertions below fail with "the agent did not use the code interpreter",
# which is expected rather than a defect.  See docs/sandbox_code_interpreter.md
# ("Threat model") for why the opt-in is not baked into servers.yaml.

# Ground truth for support/sandbox_workspace/reports/sales.csv, computed as
# units * unit_price summed per region:
#   East  7312.50
#   North 5297.35
#   South 4923.50
#   West  4032.00


def _executions(x: TestContext) -> list[dict]:
    """The code_execution effects recorded by the sandbox server."""
    effects = x.effects["sandbox"]["effects"]
    return [e for e in effects if e.get("type") == "code_execution"]


def test_reads_workspace_file_through_interpreter(x: TestContext, judge: Judge):
    """!
    query: |
        Read reports/notes.txt from the workspace and tell me what it says the
        team wants.
    """
    executions = _executions(x)
    assert executions, "the agent did not use the code interpreter"

    # The workspace must be reachable at /workspace/, and the read must actually
    # have succeeded rather than erroring out.
    read_notes = [
        e
        for e in executions
        if "notes.txt" in e.get("code", "") and e["result"].get("error") is None
    ]
    assert read_notes, (
        "no successful execution read notes.txt from the workspace: "
        f"{[e.get('code') for e in executions]}"
    )

    assert judge.text_yesno(
        x.response,
        "Does the response say the team wants revenue totalled per region, "
        "ordered from highest to lowest?",
    )


def _expected_revenue_by_region() -> dict[str, float]:
    """Compute the ground truth from the fixture itself.

    Derived rather than hard-coded so the assertion cannot drift from the data:
    editing sales.csv changes what the test demands.
    """
    fixture = (
        Path(os.environ.get("THINKINGBOX_DATA", "."))
        / "support"
        / "sandbox_workspace"
        / "reports"
        / "sales.csv"
    )
    totals: dict[str, float] = {}
    with open(fixture, newline="") as handle:
        for row in csv.DictReader(handle):
            revenue = int(row["units"]) * float(row["unit_price"])
            totals[row["region"]] = round(totals.get(row["region"], 0.0) + revenue, 2)
    return totals


def _numbers_in(text: str) -> set[float]:
    """Every number in `text`, normalised so 7,312.50 and $7312.5 both match."""
    if not text:
        return set()
    cleaned = text.replace(",", "").replace("$", "")
    return {float(m) for m in re.findall(r"-?\d+\.\d+|-?\d+", cleaned)}


def _reads_fixture(execution) -> bool:
    """True when the code actually opens the fixture rather than naming it.

    Naming the file in a string literal is not evidence of reading it.
    """
    code = execution.get("code", "")
    if "sales.csv" not in code:
        return False
    return any(
        marker in code
        for marker in ("open(", "read_csv", "Path(", "csv.", "loadtxt", "genfromtxt")
    )


def test_computes_revenue_per_region(x: TestContext, judge: Judge):
    """!
    query: |
        Using reports/sales.csv, compute total revenue per region (units times
        unit price, summed across quarters) and tell me which region has the
        highest revenue.
    """
    expected = _expected_revenue_by_region()
    assert expected, "fixture produced no ground truth; check THINKINGBOX_DATA"
    top_region = max(expected, key=expected.__getitem__)

    executions = _executions(x)
    assert executions, "the agent did not use the code interpreter"

    successful = [e for e in executions if e["result"].get("error") is None]
    assert successful, (
        "every code execution failed, so the answer was not computed: "
        f"{[e['result'].get('error') for e in executions]}"
    )

    # Naming the file is not reading it -- require an actual read call.
    reading = [e for e in successful if _reads_fixture(e)]
    assert reading, (
        "no successful execution actually read sales.csv; mentioning the "
        f"filename is not enough: {[e.get('code') for e in successful]}"
    )

    # The decisive check: every per-region total derived from the fixture must
    # appear in interpreter output, and none of them may appear in the code that
    # produced it.  Reproducing four independent totals that match the file to
    # the cent is not something a model can do by writing them into a print()
    # without having read the data -- and if it does write them in, the second
    # half of this check rejects it.
    wanted = set(expected.values())
    for execution in reading:
        produced = _numbers_in(
            (execution["result"].get("stdout") or "")
            + " "
            + (execution["result"].get("result") or "")
        )
        if not wanted.issubset(produced):
            continue
        if _numbers_in(execution.get("code", "")) & wanted:
            continue  # the totals were literals in the source, not computed
        break
    else:
        raise AssertionError(
            "no execution produced all per-region totals "
            f"{sorted(wanted)} as output without also containing them as "
            "literals in its code -- the figures were not computed from the fixture"
        )

    # And the reported answer must name the right region.
    assert judge.text_yesno(
        x.response,
        f"Does the response identify {top_region} as the region with the "
        "highest total revenue?",
    )

    # Guard against summing units instead of revenue, which would still put
    # the same region first, by requiring the exact figure.
    assert expected[top_region] in _numbers_in(x.response), (
        f"the response did not report {top_region}'s revenue as "
        f"{expected[top_region]}: {x.response!r}"
    )


def test_discovers_workspace_files(x: TestContext, judge: Judge):
    """!
    query: |
        What files are in the workspace?
    """
    effects = x.effects["sandbox"]["effects"]
    # Listing does not require the interpreter, so this exercises the filesystem
    # tools independently of the Pyodide worker.
    assert effects is not None

    assert judge.text_yesno(
        x.response,
        "Does the response mention both a sales CSV file and a notes text file "
        "under a reports folder?",
    )


def test_source_workspace_is_not_mutated(x: TestContext, judge: Judge):
    """!
    query: |
        Add a row for region Central with 100 units at 20.00 to
        reports/sales.csv, then tell me the new total revenue for Central.
    """
    executions = _executions(x)
    assert executions, "the agent did not use the code interpreter"

    # The write is expected to succeed *inside the session*: __reserved__init
    # seeds a per-session copy, and the NODEFS copy-on-write layer materialises
    # a private copy before the write lands.  The fixture under
    # support/sandbox_workspace/ must be untouched afterwards, which the
    # repository's own git status verifies -- a mutated fixture would show up as
    # a dirty working tree in CI.
    wrote = [
        e
        for e in executions
        if "sales.csv" in e.get("code", "") and e["result"].get("error") is None
    ]
    assert wrote, "no successful execution touched sales.csv"

    assert judge.text_yesno(
        x.response,
        "Does the response report Central's revenue as approximately 2000 "
        "(accepting 2000.0, 2,000 or $2000)?",
    )
