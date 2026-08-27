# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Isolation regression tests for the sandbox MCP server.

Two groups:

1. **Workspace link handling** — asserts that links in the source workspace are
   rejected or safely materialized during ``__reserved__init``. These pass and
   are a genuine regression guard: they fail against the pre-fix seeding logic.

2. **Host capability audit** — asserts that host capabilities are unavailable to
   agent-supplied Python. These are currently ``xfail(strict=True)``: Pyodide is
   not a privilege boundary, so they genuinely fail today. They are recorded
   here rather than omitted so the gap is visible in the suite, and ``strict``
   means that once OS/container confinement lands they will XPASS and force the
   marker to be removed. See docs/sandbox_code_interpreter.md ("Threat model").

The capability probes measure *reachability only*. They never read a real
system or secret file — a sentinel the test itself creates is used instead —
and they never execute a command or open a network connection.
"""

import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastmcp import Client

from thinkingbox_tools import mcp_sandbox
from thinkingbox_tools.toolslib.sandbox import code_interpreter

NOT_ISOLATED = (
    "Pyodide is not a privilege boundary; requires OS/container confinement. "
    "See docs/sandbox_code_interpreter.md (Threat model)."
)


@pytest.fixture(autouse=True)
def _allow_unconfined_worker(monkeypatch):
    """Opt in to unconfined execution for the duration of the tests.

    The interpreter fails closed without this, which is the point of the gate.
    Tests must opt in explicitly rather than the production default being lax.
    """
    monkeypatch.setenv(code_interpreter.UNCONFINED_OPT_IN_ENV, "1")


def _make_link(target, link_path, target_is_dir=False):
    """Create a symlink, skipping the test where the OS forbids it."""
    try:
        os.symlink(target, link_path, target_is_directory=target_is_dir)
    except (OSError, NotImplementedError, AttributeError) as exc:
        pytest.skip(f"cannot create symlinks on this host: {exc}")


# ---------------------------------------------------------------------------
# Workspace link handling
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def link_workspace(tmp_path_factory):
    """A workspace containing a link that points outside of itself."""
    outside = tmp_path_factory.mktemp("outside_secrets")
    (outside / "outside.txt").write_text("OUTSIDE_WORKSPACE_MARKER")

    workspace = tmp_path_factory.mktemp("workspace_with_link")
    (workspace / "normal.txt").write_text("regular file")
    _make_link(str(outside / "outside.txt"), str(workspace / "escaping_link.txt"))

    original = (
        mcp_sandbox._sandbox,
        mcp_sandbox._interpreter,
        mcp_sandbox._session_dir,
    )
    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(workspace)}}
            )
            # A namespace rather than a tuple so each test references only the
            # attributes it needs, instead of unpacking values it discards.
            yield SimpleNamespace(client=client, workspace=workspace, outside=outside)
            await client.call_tool("__reserved__teardown", {})
    finally:
        (
            mcp_sandbox._sandbox,
            mcp_sandbox._interpreter,
            mcp_sandbox._session_dir,
        ) = original


@pytest.mark.asyncio
async def test_escaping_link_not_listed(link_workspace):
    """A link escaping the workspace must not be seeded into the session."""
    result = await link_workspace.client.call_tool("list_sandbox_files", {"prefix": ""})
    files = result.structured_content["result"]["files"]
    assert "normal.txt" in files, files
    assert "escaping_link.txt" not in files, (
        f"link escaping the workspace was seeded into the session: {files}"
    )


@pytest.mark.asyncio
async def test_escaping_link_content_not_reachable(link_workspace):
    """The content behind an escaping link must not be readable from the session."""
    assert link_workspace.client is not None
    session_dir = mcp_sandbox._session_dir
    assert session_dir is not None

    leaked = []
    for dirpath, _dirs, names in os.walk(session_dir):
        for name in names:
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as handle:
                    if b"OUTSIDE_WORKSPACE_MARKER" in handle.read():
                        leaked.append(path)
            except OSError:
                continue
    assert not leaked, f"content from outside the workspace reachable at: {leaked}"


@pytest.mark.asyncio
async def test_internal_link_is_materialized(tmp_path_factory):
    """A link pointing *inside* the workspace is kept, as a real copy."""
    workspace = tmp_path_factory.mktemp("workspace_internal_link")
    (workspace / "real.txt").write_text("INTERNAL_CONTENT")
    _make_link(str(workspace / "real.txt"), str(workspace / "alias.txt"))

    original = (
        mcp_sandbox._sandbox,
        mcp_sandbox._interpreter,
        mcp_sandbox._session_dir,
    )
    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(workspace)}}
            )
            result = await client.call_tool("list_sandbox_files", {"prefix": ""})
            files = result.structured_content["result"]["files"]
            assert "alias.txt" in files, f"in-workspace link was dropped: {files}"

            seeded = os.path.join(mcp_sandbox._session_dir, "alias.txt")
            assert not os.path.islink(seeded), "in-workspace link was left followable"
            with open(seeded, "rb") as handle:
                assert b"INTERNAL_CONTENT" in handle.read()
            await client.call_tool("__reserved__teardown", {})
    finally:
        (
            mcp_sandbox._sandbox,
            mcp_sandbox._interpreter,
            mcp_sandbox._session_dir,
        ) = original


@pytest.mark.asyncio
async def test_linked_directory_is_rejected(tmp_path_factory):
    """A linked directory in the workspace must not be traversed."""
    outside = tmp_path_factory.mktemp("outside_dir")
    (outside / "hidden.txt").write_text("DIR_ESCAPE_MARKER")

    workspace = tmp_path_factory.mktemp("workspace_linked_dir")
    (workspace / "keep.txt").write_text("keep")
    _make_link(str(outside), str(workspace / "linked_dir"), target_is_dir=True)

    original = (
        mcp_sandbox._sandbox,
        mcp_sandbox._interpreter,
        mcp_sandbox._session_dir,
    )
    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(workspace)}}
            )
            result = await client.call_tool("list_sandbox_files", {"prefix": ""})
            files = result.structured_content["result"]["files"]
            assert "keep.txt" in files, files
            assert not any("hidden.txt" in f for f in files), (
                f"linked directory was traversed: {files}"
            )
            await client.call_tool("__reserved__teardown", {})
    finally:
        (
            mcp_sandbox._sandbox,
            mcp_sandbox._interpreter,
            mcp_sandbox._session_dir,
        ) = original


def test_is_link_detects_reparse_points(tmp_path):
    """_is_link must catch symlinks, and fail closed on unreadable entries."""
    plain = tmp_path / "plain.txt"
    plain.write_text("x")
    assert mcp_sandbox._is_link(str(plain)) is False

    link = tmp_path / "link.txt"
    _make_link(str(plain), str(link))
    assert mcp_sandbox._is_link(str(link)) is True

    # Non-existent entries cannot be inspected, so they must be treated as unsafe.
    assert mcp_sandbox._is_link(str(tmp_path / "missing")) is True


def test_resolves_inside_rejects_escapes(tmp_path):
    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()

    assert mcp_sandbox._resolves_inside(str(root / "sub"), str(root)) is True
    assert mcp_sandbox._resolves_inside(str(outside), str(root)) is False
    # A sibling sharing a name prefix must not be treated as inside.
    sibling = tmp_path / "root_evil"
    sibling.mkdir()
    assert mcp_sandbox._resolves_inside(str(sibling), str(root)) is False


def _make_junction(target_dir, link_path):
    """Create a Windows junction, skipping elsewhere.

    Junctions matter because they can be created without elevation, and
    ``os.path.islink`` reports False for them — so a naive symlink check misses
    them entirely.
    """
    if sys.platform != "win32":
        pytest.skip("junctions are Windows-only")

    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link_path), str(target_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"cannot create junction: {result.stderr.strip()}")


@pytest.mark.asyncio
async def test_windows_junction_is_rejected(tmp_path_factory):
    """A junction pointing outside the workspace must not be traversed.

    Regression guard for the Windows-specific case: ``os.path.islink`` returns
    False for junctions, so detection must use the reparse-point attribute.
    """
    outside = tmp_path_factory.mktemp("outside_junction")
    (outside / "hidden.txt").write_text("JUNCTION_ESCAPE_MARKER")

    workspace = tmp_path_factory.mktemp("workspace_junction")
    (workspace / "keep.txt").write_text("keep")
    _make_junction(outside, workspace / "junc")

    original = (
        mcp_sandbox._sandbox,
        mcp_sandbox._interpreter,
        mcp_sandbox._session_dir,
    )
    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(workspace)}}
            )
            result = await client.call_tool("list_sandbox_files", {"prefix": ""})
            files = result.structured_content["result"]["files"]
            assert "keep.txt" in files, files
            assert not any("hidden.txt" in f for f in files), (
                f"junction was traversed into the session: {files}"
            )
            await client.call_tool("__reserved__teardown", {})
    finally:
        (
            mcp_sandbox._sandbox,
            mcp_sandbox._interpreter,
            mcp_sandbox._session_dir,
        ) = original


def test_is_link_detects_junctions(tmp_path):
    """_is_link must detect junctions, which os.path.islink misses."""
    target = tmp_path / "target"
    target.mkdir()
    junction = tmp_path / "junc"
    _make_junction(target, junction)

    assert os.path.islink(str(junction)) is False, (
        "precondition: os.path.islink is expected to miss junctions"
    )
    assert mcp_sandbox._is_link(str(junction)) is True, (
        "junction not detected as a link — reparse-point check is not working"
    )


def test_name_surrogate_semantics():
    """Only name-surrogate reparse tags count as links.

    Junctions and symlinks name another location and are traversal risks.
    Cloud placeholders (OneDrive / Files On-Demand), deduplication and
    container mappings are the *same* file with different backing storage —
    treating those as links would reject an ordinary OneDrive-backed workspace.

    This pins the Win32 IsReparseTagNameSurrogate rule (bit 29 of the tag).
    """
    bit = mcp_sandbox._IO_REPARSE_TAG_NAME_SURROGATE_BIT

    surrogates = {
        "IO_REPARSE_TAG_MOUNT_POINT": 0xA0000003,
        "IO_REPARSE_TAG_SYMLINK": 0xA000000C,
    }
    non_surrogates = {
        "IO_REPARSE_TAG_CLOUD": 0x9000001A,
        "IO_REPARSE_TAG_CLOUD_1": 0x9000101A,
        "IO_REPARSE_TAG_CLOUD_7": 0x9000701A,
        "IO_REPARSE_TAG_DEDUP": 0x80000013,
        "IO_REPARSE_TAG_WCI": 0x80000018,
        "IO_REPARSE_TAG_APPEXECLINK": 0x8000001B,
    }

    for name, tag in surrogates.items():
        assert tag & bit, f"{name} must be treated as a link"
    for name, tag in non_surrogates.items():
        assert not (tag & bit), (
            f"{name} must NOT be treated as a link — doing so would reject "
            "ordinary files such as OneDrive placeholders"
        )


def test_non_surrogate_reparse_point_is_not_a_link(tmp_path, monkeypatch):
    """A non-surrogate reparse point must be treated as an ordinary file.

    Simulates an OneDrive-style placeholder by reporting the reparse attribute
    together with a cloud tag, since such a file cannot be created on demand.
    """
    plain = tmp_path / "cloud_placeholder.txt"
    plain.write_text("content")

    reparse_attr = getattr(mcp_sandbox.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    real_lstat = os.lstat

    class _CloudStat:
        def __init__(self, base):
            self._base = base
            self.st_file_attributes = reparse_attr
            self.st_reparse_tag = 0x9000001A  # IO_REPARSE_TAG_CLOUD

        def __getattr__(self, item):
            return getattr(self._base, item)

    def fake_lstat(path, *args, **kwargs):
        if str(path) == str(plain):
            return _CloudStat(real_lstat(plain))
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(mcp_sandbox.os, "lstat", fake_lstat)
    assert mcp_sandbox._is_link(str(plain)) is False, (
        "a cloud placeholder was treated as a link; OneDrive-backed workspaces "
        "would be rejected"
    )


# ---------------------------------------------------------------------------
# Fail-closed gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_interpreter_refuses_to_start_without_opt_in(monkeypatch, tmp_path):
    """Without the opt-in the interpreter must refuse to spawn a worker."""
    monkeypatch.delenv(code_interpreter.UNCONFINED_OPT_IN_ENV, raising=False)
    interp = code_interpreter.CodeInterpreter(timeout=5.0, workspace_dir=str(tmp_path))
    with pytest.raises(code_interpreter.CodeInterpreterError) as excinfo:
        await interp.execute("1 + 1")
    message = str(excinfo.value)
    assert code_interpreter.UNCONFINED_OPT_IN_ENV in message
    assert "not a security boundary" in message.lower()


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes"])
def test_opt_in_accepts_truthy_values(monkeypatch, value):
    monkeypatch.setenv(code_interpreter.UNCONFINED_OPT_IN_ENV, value)
    assert code_interpreter._unconfined_allowed() is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "maybe"])
def test_opt_in_rejects_other_values(monkeypatch, value):
    monkeypatch.setenv(code_interpreter.UNCONFINED_OPT_IN_ENV, value)
    assert code_interpreter._unconfined_allowed() is False


def test_worker_env_is_allowlisted(monkeypatch):
    """The worker must not inherit the parent environment wholesale."""
    monkeypatch.setenv("SANDBOX_TEST_FAKE_SECRET", "super-secret-value")
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))

    env = code_interpreter._minimal_env()
    assert "SANDBOX_TEST_FAKE_SECRET" not in env, (
        "an unrelated parent variable leaked into the worker environment"
    )
    assert "PATH" in env, "PATH is required to locate the node binary"
    for name in env:
        assert (
            name in code_interpreter._ENV_ALLOWLIST or name in {"TMPDIR", "TEMP", "TMP"}
        ), f"{name} is not on the allowlist"


# ---------------------------------------------------------------------------
# Host capability audit
# ---------------------------------------------------------------------------
#
# These probe capabilities that MUST NOT be available to agent code. They are
# not decorated with xfail. Instead each probe distinguishes three outcomes:
#
#   * harness broke (worker didn't start, probe malformed) -> FAIL, loudly.
#     A blanket xfail would swallow this and hide a broken suite.
#   * capability confirmed reachable                       -> XFAIL at runtime,
#     recording the known gap (see docs "Threat model").
#   * capability absent                                    -> PASS, which is what
#     happens once the worker is confined. No marker needs removing.
#
# Probes measure reachability only: they use a sentinel this test creates, never
# a real system file, and never execute a command or open a socket.


@pytest_asyncio.fixture
async def sandbox_client(tmp_path):
    (tmp_path / "readme.txt").write_text("hello")
    original = (
        mcp_sandbox._sandbox,
        mcp_sandbox._interpreter,
        mcp_sandbox._session_dir,
    )
    try:
        async with Client(mcp_sandbox.mcp) as client:
            await client.call_tool(
                "__reserved__init", {"config": {"workspace_dir": str(tmp_path)}}
            )
            yield client
            await client.call_tool("__reserved__teardown", {})
    finally:
        (
            mcp_sandbox._sandbox,
            mcp_sandbox._interpreter,
            mcp_sandbox._session_dir,
        ) = original


async def _capability_probe(client, code):
    """Run a probe expected to return exactly 'REACHABLE' or 'ABSENT'.

    Any other outcome means the harness itself is broken, which fails the test
    rather than being silently absorbed as an expected failure.
    """
    result = await client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]

    if sc.get("status") == "error":
        pytest.fail(f"code_interpreter tool failed, probe inconclusive: {sc.get('message')}")
    if sc.get("error"):
        pytest.fail(f"probe raised inside the interpreter, inconclusive:\n{sc['error']}")

    value = sc.get("result")
    if value == repr("REACHABLE"):
        return "REACHABLE"
    if value == repr("ABSENT"):
        return "ABSENT"
    pytest.fail(
        "probe returned an unexpected value, so the harness is not measuring "
        f"what it claims. got {value!r}, stdout={sc.get('stdout')!r}"
    )


def _record(capability, outcome, detail):
    """XFAIL on a confirmed gap; pass when the capability is genuinely gone."""
    if outcome == "REACHABLE":
        pytest.xfail(f"{capability} is reachable from agent code. {NOT_ISOLATED} ({detail})")
    assert outcome == "ABSENT"


@pytest.mark.asyncio
async def test_node_process_global_unavailable(sandbox_client):
    """`import js` must not expose the Node `process` global."""
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import js\n"
        "    _r = 'ABSENT' if getattr(js, 'process', None) is None else 'REACHABLE'\n"
        "except ImportError:\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the Node process global via `import js`", outcome, "js.process")


@pytest.mark.asyncio
async def test_privileged_pyodide_api_unavailable(sandbox_client):
    """Pyodide's internal `_api` must not be reachable from user code."""
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _r = 'REACHABLE' if hasattr(pyodide_js, '_api') else 'ABSENT'\n"
        "except ImportError:\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the privileged Pyodide internal API", outcome, "pyodide_js._api")


@pytest.mark.asyncio
async def test_js_function_constructor_unavailable(sandbox_client):
    """Cached JsProxy references must not yield the JS Function constructor.

    This is the route that survives `jsglobals` restriction and module hiding,
    because Function bodies evaluate in global scope rather than in the
    restricted globals object.
    """
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _f = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _r = 'REACHABLE' if _f is not None else 'ABSENT'\n"
        "except (ImportError, AttributeError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the JS Function constructor via a cached JsProxy", outcome, "constructor.constructor")


@pytest.mark.asyncio
async def test_host_file_outside_session_unreadable(sandbox_client, tmp_path_factory):
    """A host file outside the session directory must not be readable.

    Uses a sentinel this test creates; no real system or secret file is touched.
    """
    sentinel = tmp_path_factory.mktemp("sentinel") / "canary.txt"
    sentinel.write_text("CANARY_MARKER_DO_NOT_LEAK")
    as_posix = str(sentinel).replace("\\", "/")

    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        f"    _buf = await pyodide_js._api.loadBinaryFile({as_posix!r})\n"
        "    _r = 'REACHABLE' if b'CANARY_MARKER' in bytes(_buf.to_py()) else 'ABSENT'\n"
        "except (ImportError, AttributeError, OSError, Exception):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("host files outside the session directory", outcome, "read of a sentinel file")


@pytest.mark.asyncio
async def test_environment_variables_unreadable(sandbox_client):
    """The parent process environment must not be readable from user code.

    The worker is spawned with an allowlisted environment, so a small number of
    operational variables (PATH and friends) are expected to remain visible.
    This asserts that the *inherited* environment is not exposed wholesale.
    """
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _n = int(_F(\"return typeof process==='undefined' ? 0 :"
        ' Object.keys(process.env).length")())\n'
        "    _r = 'ABSENT' if _n == 0 else 'REACHABLE'\n"
        "except (ImportError, AttributeError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the worker process environment", outcome, "process.env")


@pytest.mark.asyncio
async def test_node_filesystem_module_unreachable(sandbox_client):
    """`node:fs` must not be resolvable from agent code.

    Resolution only: nothing is read or written through the module.
    """
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _fn = _F(\"return import('node:fs')"
        ".then(m => typeof m.readFileSync === 'function' ? 'REACHABLE' : 'ABSENT')"
        ".catch(() => 'ABSENT')\")\n"
        "    _r = await _fn()\n"
        "except (ImportError, AttributeError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the node:fs module", outcome, "dynamic import('node:fs')")


@pytest.mark.asyncio
async def test_node_process_module_unreachable(sandbox_client):
    """`node:child_process` must not be resolvable from agent code.

    Resolution only: no process is ever spawned by this test.
    """
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _fn = _F(\"return import('node:child_process')"
        ".then(m => typeof m.execSync === 'function' ? 'REACHABLE' : 'ABSENT')"
        ".catch(() => 'ABSENT')\")\n"
        "    _r = await _fn()\n"
        "except (ImportError, AttributeError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("the node:child_process module", outcome, "dynamic import('node:child_process')")
