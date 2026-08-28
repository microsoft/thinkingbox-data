# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

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


def _states_total(text: str) -> bool:
    """True when the text contains East's revenue in any plausible formatting."""
    if not text:
        return False
    normalized = text.replace(",", "").replace("$", "")
    return any(form in normalized for form in ("7312.5", "7312.50"))


def test_computes_revenue_per_region(x: TestContext, judge: Judge):
    """!
    query: |
        Using reports/sales.csv, compute total revenue per region (units times
        unit price, summed across quarters) and tell me which region has the
        highest revenue.
    """
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

    # The decisive check: the figure must come *out* of the interpreter while
    # being absent from the code that produced it.  A response is only credible
    # if the number was computed from the fixture, and an execution such as
    # `print("sales.csv: East 7312.50")` would satisfy every check above while
    # reading nothing -- so require the value in the output and not in the source.
    computed = [
        e
        for e in reading
        if _states_total(
            (e["result"].get("stdout") or "") + " " + (e["result"].get("result") or "")
        )
        and not _states_total(e.get("code", ""))
    ]
    assert computed, (
        "East's revenue never appeared in interpreter output that did not "
        "already contain it as a literal -- the figure was hard-coded rather "
        "than computed from the fixture"
    )

    # East is the correct answer (7312.50).
    assert judge.text_yesno(
        x.response,
        "Does the response identify East as the region with the highest total "
        "revenue?",
    )

    # Guard against summing units instead of revenue, which would still put East
    # first, by requiring the figure itself.
    assert _states_total(x.response), (
        f"the response did not report East's revenue as 7312.50: {x.response!r}"
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
