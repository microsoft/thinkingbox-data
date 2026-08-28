# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from thinkingbox.common import Judge, TestContext

"""!
scenario: sandbox_code_interpreter
"""

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


def test_computes_revenue_per_region(x: TestContext, judge: Judge):
    """!
    query: |
        Using reports/sales.csv, compute total revenue per region (units times
        unit price, summed across quarters) and tell me which region has the
        highest revenue.
    """
    executions = _executions(x)
    assert executions, "the agent did not use the code interpreter"

    # Every execution the agent kept should be error-free by the end; at minimum
    # one must have succeeded, otherwise any correct-looking answer was invented.
    successful = [e for e in executions if e["result"].get("error") is None]
    assert successful, (
        "every code execution failed, so the answer was not computed: "
        f"{[e['result'].get('error') for e in executions]}"
    )

    # The figures must come from code, not from the model doing mental math.
    assert any(
        "sales.csv" in e.get("code", "") for e in successful
    ), "no successful execution referenced sales.csv"

    # East is the correct answer (7312.50).
    assert judge.text_yesno(
        x.response,
        "Does the response identify East as the region with the highest total "
        "revenue?",
    )

    # Guard against the most likely wrong answer: summing units instead of
    # revenue would still make East highest, so check the figure was reported.
    assert judge.text_yesno(
        x.response,
        "Does the response report East's total revenue as approximately 7312.50 "
        "(accepting 7312.5, 7,312.50 or $7312.50)?",
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
