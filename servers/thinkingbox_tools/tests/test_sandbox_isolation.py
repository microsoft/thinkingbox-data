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
import sys

import pytest
import pytest_asyncio
from fastmcp import Client

from thinkingbox_tools import mcp_sandbox

NOT_ISOLATED = (
    "Pyodide is not a privilege boundary; requires OS/container confinement. "
    "See docs/sandbox_code_interpreter.md (Threat model)."
)


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
            yield client, workspace, outside
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
    client, _workspace, _outside = link_workspace
    result = await client.call_tool("list_sandbox_files", {"prefix": ""})
    files = result.structured_content["result"]["files"]
    assert "normal.txt" in files, files
    assert "escaping_link.txt" not in files, (
        f"link escaping the workspace was seeded into the session: {files}"
    )


@pytest.mark.asyncio
async def test_escaping_link_content_not_reachable(link_workspace):
    """The content behind an escaping link must not be readable from the session."""
    _client, _workspace, _outside = link_workspace
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
    import subprocess

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


# ---------------------------------------------------------------------------
# Host capability audit
# ---------------------------------------------------------------------------


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


async def _probe(client, code):
    """Run a probe and return its repr'd result, or the surfaced error."""
    result = await client.call_tool("code_interpreter", {"code": code})
    sc = result.structured_content["result"]
    if sc.get("status") == "error":
        return f"tool-error:{sc.get('message')}"
    return sc.get("result")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_node_process_global_unavailable(sandbox_client):
    """`import js` must not expose the Node `process` global."""
    code = (
        "try:\n"
        "    import js\n"
        "    _r = 'ABSENT' if getattr(js, 'process', None) is None else 'REACHABLE'\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_privileged_pyodide_api_unavailable(sandbox_client):
    """Pyodide's internal `_api` must not be reachable from user code."""
    code = (
        "try:\n"
        "    import pyodide_js\n"
        "    _r = 'REACHABLE' if hasattr(pyodide_js, '_api') else 'ABSENT'\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_js_function_constructor_unavailable(sandbox_client):
    """Cached JsProxy references must not yield the JS Function constructor.

    This is the route that survives `jsglobals` restriction and module hiding,
    because Function bodies evaluate in global scope.
    """
    code = (
        "try:\n"
        "    import pyodide_js\n"
        "    _f = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _r = 'REACHABLE' if _f is not None else 'ABSENT'\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_host_file_outside_session_unreadable(sandbox_client, tmp_path_factory):
    """A host file outside the session dir must not be readable.

    Uses a sentinel this test creates; no real system file is touched.
    """
    sentinel_dir = tmp_path_factory.mktemp("sentinel")
    sentinel = sentinel_dir / "canary.txt"
    sentinel.write_text("CANARY_MARKER_DO_NOT_LEAK")
    as_posix = str(sentinel).replace("\\", "/")

    code = (
        "try:\n"
        "    import pyodide_js\n"
        f"    _buf = await pyodide_js._api.loadBinaryFile({as_posix!r})\n"
        "    _r = 'REACHABLE' if b'CANARY_MARKER' in bytes(_buf.to_py()) else 'ABSENT'\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_environment_variables_unreadable(sandbox_client):
    """The parent process environment must not be readable from user code."""
    code = (
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _n = _F(\"return typeof process==='undefined' ? 0 : Object.keys(process.env).length\")()\n"
        "    _r = 'ABSENT' if int(_n) == 0 else 'REACHABLE'\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason=NOT_ISOLATED)
async def test_node_builtin_modules_unreachable(sandbox_client):
    """node:fs and node:child_process must not be resolvable.

    Resolution only — no file is read and no process is spawned.
    """
    code = (
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        "    _fn = _F(\"return import('node:child_process')"
        ".then(m => typeof m.execSync === 'function' ? 'REACHABLE' : 'ABSENT')"
        ".catch(() => 'ABSENT')\")\n"
        "    _r = await _fn()\n"
        "except Exception:\n"
        "    _r = 'ABSENT'\n"
        "_r"
    )
    assert await _probe(sandbox_client, code) == repr("ABSENT")
