# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the sandbox MCP server — filesystem tools and code interpreter workspace access."""

import asyncio

import pytest
import pytest_asyncio
from fastmcp import Client

from thinkingbox_tools import mcp_sandbox
from thinkingbox_tools.toolslib.sandbox import code_interpreter

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
# Each test gets a fresh session: __reserved__init copies tmp_path into a new
# temp directory, wiring both the filesystem tools and the Pyodide worker to
# that isolated copy.  __reserved__teardown removes it.  The Pyodide worker
# starts lazily on the first code_interpreter call, so filesystem-only tests
# pay no startup cost.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _allow_unconfined_worker(monkeypatch):
    """Opt in to unconfined execution for these tests.

    The interpreter fails closed without this (Pyodide is not a privilege
    boundary), so the test suite must opt in explicitly rather than the
    production default being permissive.
    """
    monkeypatch.setenv(code_interpreter.UNCONFINED_OPT_IN_ENV, "1")


@pytest_asyncio.fixture
async def sandbox_client(tmp_path):
    """Provide a sandbox session backed by a temporary workspace with known test files."""
    (tmp_path / "readme.txt").write_text("Hello, sandbox!")
    (tmp_path / "data.csv").write_text("name,value\nalice,1\nbob,2\n")
    (tmp_path / "report.pdf").write_bytes(b"%PDF-1.4 fake pdf content")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "notes.txt").write_text("notes inside subdir")

    original_sandbox = mcp_sandbox._sandbox
    original_interp = mcp_sandbox._interpreter
    original_session_dir = mcp_sandbox._session_dir

    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(tmp_path)}}
            )
            yield client
            await client.call_tool("__reserved__teardown", {})
    finally:
        mcp_sandbox._sandbox = original_sandbox
        mcp_sandbox._interpreter = original_interp
        mcp_sandbox._session_dir = original_session_dir


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tools_list(sandbox_client):
    tools = await sandbox_client.list_tools()
    names = [t.name for t in tools]
    assert "list_sandbox_files" in names
    assert "search_sandbox_files" in names
    assert "code_interpreter" in names


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_files_all(sandbox_client):
    result = await sandbox_client.call_tool("list_sandbox_files", {"prefix": ""})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    files = sc["files"]
    assert "readme.txt" in files
    assert "data.csv" in files
    assert "report.pdf" in files
    assert "subdir/notes.txt" in files


@pytest.mark.asyncio
async def test_list_files_prefix(sandbox_client):
    result = await sandbox_client.call_tool("list_sandbox_files", {"prefix": "subdir"})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["files"] == ["subdir/notes.txt"]


@pytest.mark.asyncio
async def test_list_files_nonexistent_prefix(sandbox_client):
    result = await sandbox_client.call_tool(
        "list_sandbox_files", {"prefix": "no_such_dir"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["files"] == []


@pytest.mark.asyncio
async def test_list_files_rejects_parent_traversal(sandbox_client):
    """Prefixes that resolve outside the workspace must not leak host paths."""
    for prefix in ("..", "../", "../..", "subdir/../.."):
        result = await sandbox_client.call_tool(
            "list_sandbox_files", {"prefix": prefix}
        )
        sc = result.structured_content["result"]
        assert sc["status"] == "ok"
        assert sc["files"] == [], f"prefix {prefix!r} leaked files: {sc['files']}"


# ---------------------------------------------------------------------------
# search_files
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_files_by_extension(sandbox_client):
    result = await sandbox_client.call_tool(
        "search_sandbox_files", {"pattern": "*.csv"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["files"] == ["data.csv"]


@pytest.mark.asyncio
async def test_search_files_recursive(sandbox_client):
    result = await sandbox_client.call_tool(
        "search_sandbox_files", {"pattern": "**/*.txt"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert "readme.txt" in sc["files"]
    assert "subdir/notes.txt" in sc["files"]


@pytest.mark.asyncio
async def test_search_files_no_match(sandbox_client):
    result = await sandbox_client.call_tool(
        "search_sandbox_files", {"pattern": "*.xyz"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["files"] == []


@pytest.mark.asyncio
async def test_search_files_rejects_parent_traversal(sandbox_client):
    """Glob patterns that walk outside the workspace must not leak host paths."""
    for pattern in ("../*", "../**/*", "../../*"):
        result = await sandbox_client.call_tool(
            "search_sandbox_files", {"pattern": pattern}
        )
        sc = result.structured_content["result"]
        assert sc["status"] == "ok"
        assert sc["files"] == [], f"pattern {pattern!r} leaked files: {sc['files']}"


# ---------------------------------------------------------------------------
# code_interpreter — workspace file access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_code_interpreter_reads_text_file(sandbox_client):
    """Code can open and read a plain text file from /workspace/."""
    code = "open('/workspace/readme.txt').read()"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok", sc.get("error") or sc
    assert sc["error"] is None
    assert sc["result"] == repr("Hello, sandbox!")


@pytest.mark.asyncio
async def test_code_interpreter_reads_csv_with_pandas(sandbox_client):
    """Code can load a CSV from /workspace/ into a pandas DataFrame."""
    code = (
        "import pandas as pd\n"
        "df = pd.read_csv('/workspace/data.csv')\n"
        "list(df['name'])"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is None
    assert "alice" in sc["result"]
    assert "bob" in sc["result"]


@pytest.mark.asyncio
async def test_code_interpreter_reads_subdir_file(sandbox_client):
    """Code can access files in subdirectories under /workspace/."""
    code = "open('/workspace/subdir/notes.txt').read()"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is None
    assert sc["result"] == repr("notes inside subdir")


# ---------------------------------------------------------------------------
# Isolation — writes go to the session copy, not the original workspace
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_code_interpreter_can_write_file(sandbox_client):
    """Code can write a new file into /workspace/ (the session copy)."""
    code = "open('/workspace/output.txt', 'w').write('written by agent')"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is None


@pytest.mark.asyncio
async def test_written_file_visible_to_list_files(sandbox_client):
    """A file written via code_interpreter is visible to list_files in the same session."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/output.txt', 'w').write('hello')"},
    )
    result = await sandbox_client.call_tool("list_sandbox_files", {"prefix": ""})
    sc = result.structured_content["result"]
    assert "output.txt" in sc["files"]


@pytest.mark.asyncio
async def test_original_workspace_not_modified(sandbox_client, tmp_path):
    """Writing a new file via code_interpreter does not modify the original workspace_dir."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/injected.txt', 'w').write('should not exist')"},
    )
    assert not (tmp_path / "injected.txt").exists()


# ---------------------------------------------------------------------------
# Copy-on-write — overwriting existing files is isolated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_overwrite_existing_file_isolated(sandbox_client, tmp_path):
    """Overwriting an existing workspace file does not affect the original inode."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/readme.txt', 'w').write('overwritten')"},
    )
    assert (tmp_path / "readme.txt").read_text() == "Hello, sandbox!"
    result = await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/readme.txt', 'r').read()"},
    )
    sc = result.structured_content["result"]
    assert sc["result"] == repr("overwritten")


@pytest.mark.asyncio
async def test_overwrite_visible_within_session(sandbox_client):
    """After overwriting, the updated content is readable in the same session."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/readme.txt', 'w').write('new content')"},
    )
    result = await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/readme.txt').read()"},
    )
    sc = result.structured_content["result"]
    assert sc["error"] is None
    assert sc["result"] == repr("new content")


@pytest.mark.asyncio
async def test_append_existing_file_isolated(sandbox_client, tmp_path):
    """Appending to an existing workspace file does not affect the original."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/readme.txt', 'a').write(' appended')"},
    )
    assert (tmp_path / "readme.txt").read_text() == "Hello, sandbox!"


@pytest.mark.asyncio
async def test_os_open_truncate_without_o_creat(sandbox_client, tmp_path):
    """`os.open(path, O_WRONLY | O_TRUNC)` (no O_CREAT) succeeds on a seeded
    workspace file and does not touch the source.

    Regression: materializeSymlink used to unlink the symlink without
    recreating the host file in the truncate path, so this call landed on a
    missing file and raised ENOENT.
    """
    code = (
        "import os\n"
        "fd = os.open('/workspace/readme.txt', os.O_WRONLY | os.O_TRUNC)\n"
        "try:\n"
        "    os.write(fd, b'truncated')\n"
        "finally:\n"
        "    os.close(fd)\n"
        "open('/workspace/readme.txt').read()"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["error"] is None, sc["error"]
    assert sc["result"] == repr("truncated")
    assert (tmp_path / "readme.txt").read_text() == "Hello, sandbox!"


# ---------------------------------------------------------------------------
# code_interpreter — stdout / stderr capture
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_stdout(sandbox_client):
    result = await sandbox_client.call_tool(
        "code_interpreter", {"code": "print('hello world')"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["stdout"] == "hello world\n"
    assert sc["stderr"] == ""
    assert sc["error"] is None


@pytest.mark.asyncio
async def test_execute_stderr(sandbox_client):
    code = "import sys; sys.stderr.write('err msg')"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["stderr"] == "err msg"
    assert sc["error"] is None


# ---------------------------------------------------------------------------
# code_interpreter — expression result capture (Jupyter-style last-expression)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_expression_result(sandbox_client):
    result = await sandbox_client.call_tool("code_interpreter", {"code": "1 + 1"})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["result"] == "2"
    assert sc["stdout"] == ""


@pytest.mark.asyncio
async def test_execute_statement_no_result(sandbox_client):
    """Assignments are statements — result should be None."""
    result = await sandbox_client.call_tool(
        "code_interpreter", {"code": "_stmt_var = 42"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["result"] is None


@pytest.mark.asyncio
async def test_execute_stdout_and_expression(sandbox_client):
    """Print followed by a trailing expression — both captured."""
    code = "print('hi')\n2 + 2"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["stdout"] == "hi\n"
    assert sc["result"] == "4"


# ---------------------------------------------------------------------------
# code_interpreter — error handling stays in 'error' field, tool doesn't raise
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_runtime_error(sandbox_client):
    result = await sandbox_client.call_tool("code_interpreter", {"code": "1 / 0"})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is not None
    assert "ZeroDivisionError" in sc["error"]
    assert sc["result"] is None


@pytest.mark.asyncio
async def test_execute_name_error(sandbox_client):
    result = await sandbox_client.call_tool(
        "code_interpreter", {"code": "_undefined_xyz"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is not None
    assert "NameError" in sc["error"]


@pytest.mark.asyncio
async def test_execute_syntax_error(sandbox_client):
    result = await sandbox_client.call_tool("code_interpreter", {"code": "def f(:"})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is not None
    assert "SyntaxError" in sc["error"]


# ---------------------------------------------------------------------------
# code_interpreter — multiline code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_multiline(sandbox_client):
    code = "def _add(a, b):\n    return a + b\n_add(3, 4)"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["result"] == "7"
    assert sc["error"] is None


# ---------------------------------------------------------------------------
# code_interpreter — state persistence (REPL semantics across calls)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_state_persistence(sandbox_client):
    """Variables defined in one call are visible in subsequent calls."""
    await sandbox_client.call_tool("code_interpreter", {"code": "_persist_x = 100"})
    result = await sandbox_client.call_tool(
        "code_interpreter", {"code": "_persist_x * 2"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["result"] == "200"


@pytest.mark.asyncio
async def test_import_persists(sandbox_client):
    """Imports made in one call are available in subsequent calls."""
    await sandbox_client.call_tool("code_interpreter", {"code": "import math as _math"})
    result = await sandbox_client.call_tool(
        "code_interpreter", {"code": "_math.floor(2.9)"}
    )
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["result"] == "2"


# ---------------------------------------------------------------------------
# code_interpreter — pre-installed packages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_numpy_and_pandas_available(sandbox_client):
    """numpy and pandas are pre-installed and usable."""
    code = (
        "import numpy as np, pandas as pd\n"
        "s = pd.Series(np.array([1, 2, 3]))\n"
        "int(s.sum())"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is None
    assert sc["result"] == "6"


# Distribution name on PyPI / pyodide-lock → top-level module name.
# Kept aligned with BUNDLED_PACKAGES + PYPI_PACKAGES in pyodide_worker.mjs.
# Excluded from preload (and this test) because their transitive deps require
# native binaries that pyodide does not provide:
#   - markitdown -> magika -> onnxruntime
#   - pdfplumber -> pypdfium2
PREINSTALLED_LIBRARIES = [
    # Bundled in pyodide-lock.json (loaded via pyodide.loadPackage).
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("beautifulsoup4", "bs4"),
    ("Jinja2", "jinja2"),
    ("sympy", "sympy"),
    ("altair", "altair"),
    ("mpmath", "mpmath"),
    ("lxml", "lxml"),
    ("Pillow", "PIL"),
    # Installed from PyPI via micropip at worker startup.
    ("openpyxl", "openpyxl"),
    ("xlsxwriter", "xlsxwriter"),
    ("markdownify", "markdownify"),
    ("mammoth", "mammoth"),
    ("pypdf", "pypdf"),
    ("pdfminer.six", "pdfminer"),
    ("tabulate", "tabulate"),
    ("plotly", "plotly"),
    ("python-docx", "docx"),
    ("python-pptx", "pptx"),
    ("reportlab", "reportlab"),
]


@pytest.mark.asyncio
async def test_preinstalled_libraries_importable(sandbox_client):
    """Every library preloaded by pyodide_worker.mjs imports cleanly in user code.

    Bundled packages (numpy, pandas, ...) load from pyodide's local wheel set
    inside node_modules/pyodide/.  PyPI-only packages (openpyxl, mammoth, ...)
    install from file:// URLs pointing at wheels/, which are pre-downloaded by
    the `npm install` postinstall hook (scripts/download-wheels.mjs).  If a
    wheel is missing locally, micropip falls back to PyPI at worker startup.
    """
    import_lines = "\n".join(f"import {mod}" for _, mod in PREINSTALLED_LIBRARIES)
    name_tuple = (
        "(" + ", ".join(f"{mod}.__name__" for _, mod in PREINSTALLED_LIBRARIES) + ",)"
    )
    code = f"{import_lines}\n{name_tuple}"

    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert sc["error"] is None, sc["error"]
    for _, mod in PREINSTALLED_LIBRARIES:
        assert f"'{mod}'" in sc["result"], f"missing module {mod} in {sc['result']}"


@pytest.mark.asyncio
async def test_pyodide_lazy_autoload_on_import(sandbox_client):
    """A pyodide-bundled package not in PREINSTALLED_LIBRARIES auto-loads on first import.

    Verifies the pyodide.loadPackagesFromImports() call wired into the worker's
    request loop — without it, this import would raise ModuleNotFoundError.
    """
    code = "import scipy; scipy.__name__"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok", sc.get("error") or sc
    assert sc["error"] is None, sc["error"]
    assert "'scipy'" in sc["result"]


@pytest.mark.asyncio
async def test_concurrent_execute_calls_are_serialized(sandbox_client):
    """Two concurrent execute() coroutines must not collide on the worker stdio.

    The Node worker speaks a strict request/response protocol on a single
    stdin/stdout pair.  Without serialization, asyncio.gather()'d calls
    would interleave writes and race on `StreamReader.readline()` —
    asyncio raises `RuntimeError: readline() called while another
    coroutine is already waiting for incoming data` on the second
    concurrent reader.  Bypass FastMCP and hit the interpreter directly
    so the race is actually reachable (FastMCP may serialize at its own
    transport layer).
    """
    # Warm up the worker so the race is on execute(), not _ensure_started().
    await sandbox_client.call_tool("code_interpreter", {"code": "1"})
    interpreter = mcp_sandbox._interpreter
    assert interpreter is not None

    code_a = "'A' * 5000"
    code_b = "'B' * 5000"
    a, b = await asyncio.gather(
        interpreter.execute(code_a),
        interpreter.execute(code_b),
    )

    assert a.error is None, a.error
    assert b.error is None, b.error
    assert a.result == repr("A" * 5000)
    assert b.result == repr("B" * 5000)


@pytest.mark.asyncio
async def test_top_level_await_micropip_install(sandbox_client):
    """Agent-supplied `await micropip.install(...)` should succeed.

    The documentation and the `code_interpreter` MCP tool description tell
    agents to add new packages via `await micropip.install("name")`.  The
    worker must therefore accept top-level await in user code, which a plain
    `exec(compile(...))` does not — `PyCF_ALLOW_TOP_LEVEL_AWAIT` (0x2000) is
    required, and any returned coroutine must be awaited.
    """
    code = "import micropip\nawait micropip.install('cowsay')\nimport cowsay\ncowsay.__name__"
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok", sc.get("error") or sc
    assert sc["error"] is None, sc["error"]
    assert "'cowsay'" in sc["result"]


# ---------------------------------------------------------------------------
# Effects tracking — calls __reserved__init so placed last
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_effects_tracking(sandbox_client):
    """Effects list records every execution with its outputs."""
    await sandbox_client.call_tool("__reserved__init", {"config": {}})

    await sandbox_client.call_tool("code_interpreter", {"code": "print('tracked')"})

    effects_result = await sandbox_client.call_tool("__reserved__geteffects", {})
    ec = effects_result.structured_content
    assert len(ec["effects"]) == 1
    effect = ec["effects"][0]
    assert effect["type"] == "code_execution"
    assert effect["code"] == "print('tracked')"
    assert effect["result"]["stdout"] == "tracked\n"
    assert effect["result"]["error"] is None


@pytest.mark.asyncio
async def test_effects_reset_on_init(sandbox_client):
    """__reserved__init clears the effects list."""
    await sandbox_client.call_tool("code_interpreter", {"code": "1 + 1"})
    await sandbox_client.call_tool("__reserved__init", {"config": {}})

    effects_result = await sandbox_client.call_tool("__reserved__geteffects", {})
    ec = effects_result.structured_content
    assert ec["effects"] == []


# ---------------------------------------------------------------------------
# Workspace write boundary — writes must not escape to the host filesystem
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_to_absolute_host_path_does_not_affect_host(
    sandbox_client, tmp_path_factory
):
    """Writing to an absolute host path outside /workspace does not create a host file."""
    outside_dir = tmp_path_factory.mktemp("outside_abs")
    target = outside_dir / "escape.txt"
    code = f"open({str(target)!r}, 'w').write('escaped')"
    await sandbox_client.call_tool("code_interpreter", {"code": code})
    assert not target.exists()


@pytest.mark.asyncio
async def test_path_traversal_does_not_escape_to_host(sandbox_client, tmp_path):
    """`/workspace/../foo.txt` does not escape to the host filesystem."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "open('/workspace/../traversal_escape.txt', 'w').write('escaped')"},
    )
    assert not (tmp_path / "traversal_escape.txt").exists()
    assert not (tmp_path.parent / "traversal_escape.txt").exists()


@pytest.mark.asyncio
async def test_relative_path_traversal_does_not_escape_to_host(
    sandbox_client, tmp_path
):
    """`../foo.txt` written from inside /workspace does not escape to the host."""
    code = (
        "import os\n"
        "os.chdir('/workspace')\n"
        "open('../relative_escape.txt', 'w').write('escaped')\n"
    )
    await sandbox_client.call_tool("code_interpreter", {"code": code})
    assert not (tmp_path / "relative_escape.txt").exists()
    assert not (tmp_path.parent / "relative_escape.txt").exists()


@pytest.mark.asyncio
async def test_unlink_in_workspace_does_not_affect_source(sandbox_client, tmp_path):
    """Deleting a file under /workspace does not delete the original source file."""
    await sandbox_client.call_tool(
        "code_interpreter",
        {"code": "import os; os.unlink('/workspace/readme.txt')"},
    )
    assert (tmp_path / "readme.txt").exists()
    assert (tmp_path / "readme.txt").read_text() == "Hello, sandbox!"


@pytest.mark.asyncio
async def test_host_files_outside_workspace_not_readable(
    sandbox_client, tmp_path_factory
):
    """Files outside /workspace on the host are not readable via absolute paths."""
    outside_dir = tmp_path_factory.mktemp("outside_read")
    secret = outside_dir / "secret.txt"
    secret.write_text("HOST_SECRET_MARKER")
    code = (
        "try:\n"
        f"    _c = open({str(secret)!r}).read()\n"
        "except (FileNotFoundError, OSError):\n"
        "    _c = '<isolated>'\n"
        "_c"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["status"] == "ok"
    assert "HOST_SECRET_MARKER" not in (sc["result"] or "")


@pytest.mark.asyncio
async def test_symlink_to_existing_target_does_not_escape(
    sandbox_client, tmp_path_factory
):
    """User code cannot create a symlink under /workspace pointing to an
    existing host file and use it to overwrite that host file.

    Both halves matter:
      - NODEFS.node_ops.symlink must raise (protection actually fires).
      - The host file must remain untouched.
    Asserting only the second would also pass for any unrelated failure in
    user code, which would silently hide a broken protection.
    """
    outside_dir = tmp_path_factory.mktemp("outside_symlink_existing")
    target = outside_dir / "victim.txt"
    target.write_text("ORIGINAL")

    code = (
        "import os\n"
        f"os.symlink({str(target)!r}, '/workspace/link')\n"
        f"open('/workspace/link', 'w').write('overwritten')\n"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["error"] is not None, sc
    assert "PermissionError" in sc["error"], sc["error"]
    assert target.read_text() == "ORIGINAL"


@pytest.mark.asyncio
async def test_symlink_to_nonexistent_target_does_not_escape(
    sandbox_client, tmp_path_factory
):
    """User code cannot create a symlink under /workspace pointing to a
    nonexistent host path and use it to materialize a file at that path.

    Both halves matter:
      - NODEFS.node_ops.symlink must raise (protection actually fires).
      - The host path must not be created.
    """
    outside_dir = tmp_path_factory.mktemp("outside_symlink_dangling")
    target = outside_dir / "should_not_be_created.txt"
    assert not target.exists()

    code = (
        "import os\n"
        f"os.symlink({str(target)!r}, '/workspace/dangling')\n"
        f"open('/workspace/dangling', 'w').write('escaped')\n"
    )
    result = await sandbox_client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    assert sc["error"] is not None, sc
    assert "PermissionError" in sc["error"], sc["error"]
    assert not target.exists()
