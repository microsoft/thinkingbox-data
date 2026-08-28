# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Isolation regression tests for the sandbox MCP server.

Two groups:

1. **Workspace link handling** — asserts that links in the source workspace are
   rejected or safely materialized during ``__reserved__init``. These pass and
   are a genuine regression guard: they fail against the pre-fix seeding logic.

2. **Host capability audit** — asserts that host capabilities are unavailable to
   agent-supplied Python. They currently fail, because Pyodide is not a
   privilege boundary. They are *not* blanket-``xfail``ed: each probe fails
   loudly if it cannot run, records an expected failure only when a capability
   is *confirmed* reachable, and simply passes once the capability is gone.
   See docs/sandbox_code_interpreter.md ("Threat model").

The capability probes assert on observable effects (bytes read, a file written,
a secret retrieved) rather than on whether an API name exists, and they catch
only the specific errors a confining policy would raise. An unexpected worker,
import or loader error propagates and fails the test, so a broken probe is
never mistaken for confinement. Probes stay inside directories pytest created:
no real system or secret file is read, and nothing outside the temp directory
is modified.
"""

import asyncio
import json
import os
import subprocess
import sys
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastmcp import Client

from thinkingbox_tools import mcp_sandbox
from thinkingbox_tools.toolslib.sandbox import code_interpreter
from thinkingbox_tools.toolslib.sandbox.sandbox import Sandbox

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
        assert name in code_interpreter._ENV_ALLOWLIST, f"{name} is not on the allowlist"


def test_worker_tmp_is_not_inherited(monkeypatch, tmp_path):
    """TMPDIR/TEMP/TMP must point at a worker-owned dir, not the parent's."""
    monkeypatch.setenv("TMPDIR", "/parent/tmp")
    monkeypatch.setenv("TEMP", r"C:\parent\temp")
    monkeypatch.setenv("TMP", r"C:\parent\temp")

    # Without a worker-owned directory the variables are omitted entirely.
    env = code_interpreter._minimal_env()
    for name in ("TMPDIR", "TEMP", "TMP"):
        assert name not in env, f"{name} was forwarded from the parent"

    # With one, they point at it rather than at the parent's value.
    worker_tmp = str(tmp_path / "worker_tmp")
    env = code_interpreter._minimal_env(worker_tmp)
    for name in ("TMPDIR", "TEMP", "TMP"):
        assert env[name] == worker_tmp, f"{name} did not point at the worker dir"


# ---------------------------------------------------------------------------
# Worker protocol robustness
# ---------------------------------------------------------------------------


class _FakeStdout:
    """Minimal StreamReader stand-in returning canned frames."""

    def __init__(self, frames):
        self._frames = list(frames)

    async def readline(self):
        if not self._frames:
            return b""
        frame = self._frames.pop(0)
        if isinstance(frame, Exception):
            raise frame
        return frame


class _FakeStdin:
    def write(self, _data):
        pass

    async def drain(self):
        pass

    def close(self):
        pass


class _FakeProcess:
    def __init__(self, frames):
        self.stdout = _FakeStdout(frames)
        self.stdin = _FakeStdin()
        self.returncode = None
        self.killed = False

    def kill(self):
        self.killed = True
        self.returncode = -9

    async def wait(self):
        return self.returncode


def _interp_with(frames):
    """A CodeInterpreter wired to a fake worker emitting `frames`."""
    interp = code_interpreter.CodeInterpreter(timeout=5.0)
    proc = _FakeProcess(frames)
    interp._process = proc
    return interp, proc


@pytest.mark.asyncio
async def test_malformed_frame_resets_worker():
    """A non-JSON frame must reset the worker, not desync the stream.

    Without the reset, the malformed line raises while the real response stays
    buffered, and the *next* execute() returns the previous call's result.
    """
    real = json.dumps({"stdout": "correct", "stderr": "", "result": None, "error": None})
    interp, proc = _interp_with([b"not json at all\n", real.encode() + b"\n"])

    with pytest.raises(code_interpreter.CodeInterpreterError) as excinfo:
        await interp.execute("1")
    assert "out of sync" in str(excinfo.value)
    assert proc.killed, "worker was left running with a desynchronized stream"
    assert interp._process is None, "next call would reuse the poisoned stream"


@pytest.mark.asyncio
async def test_non_object_frame_resets_worker():
    """A JSON frame that is not an object is also a protocol violation."""
    interp, proc = _interp_with([b'"just a string"\n'])
    with pytest.raises(code_interpreter.CodeInterpreterError):
        await interp.execute("1")
    assert proc.killed
    assert interp._process is None


@pytest.mark.asyncio
async def test_oversized_frame_resets_worker():
    """An over-limit frame must surface a clear error and reset the worker.

    asyncio's StreamReader raises ValueError rather than returning the line, and
    the unread remainder would otherwise be parsed as the next response.
    """
    interp, proc = _interp_with(
        [ValueError("Separator is found, but chunk is longer than limit")]
    )
    with pytest.raises(code_interpreter.CodeInterpreterError) as excinfo:
        await interp.execute("print('x' * 10_000_000)")
    message = str(excinfo.value)
    assert "larger than" in message and "reset" in message
    assert proc.killed
    assert interp._process is None


def test_stream_limit_exceeds_asyncio_default():
    """The configured limit must be above asyncio's 64 KiB default.

    A single print() of a large DataFrame exceeds 64 KiB, so the default would
    make ordinary analysis fail.
    """
    import asyncio.streams

    assert code_interpreter.CodeInterpreter.STREAM_LIMIT > asyncio.streams._DEFAULT_LIMIT
    assert code_interpreter.CodeInterpreter.STREAM_LIMIT >= 8 * 1024 * 1024


@pytest.mark.asyncio
async def test_cancelled_execute_resets_worker():
    """Cancelling a call must reset the worker, not leave its reply buffered.

    The worker still writes a reply for the abandoned request.  If the process
    stays attached, the next execute() reads that stale frame and returns the
    previous call's output -- a silently wrong answer rather than an error.
    CancelledError is a BaseException, so nothing upstream catches this.
    """

    class _ParkingStdout:
        def __init__(self):
            self.release = asyncio.Event()
            self.queued = []

        async def readline(self):
            if not self.release.is_set():
                await self.release.wait()
            return self.queued.pop(0) if self.queued else b""

    interp = code_interpreter.CodeInterpreter(timeout=30.0)
    proc = _FakeProcess([])
    proc.stdout = _ParkingStdout()
    interp._process = proc

    task = asyncio.create_task(interp.execute("call_1()"))
    await asyncio.sleep(0.05)
    task.cancel()

    # Await explicitly rather than relying on a bare `await task` inside
    # pytest.raises: naming the outcome states what is being asserted, and a
    # bare await reads as a no-op statement to static analysis.
    cancelled = False
    try:
        await task
    except asyncio.CancelledError:
        cancelled = True
    assert cancelled, "execute() swallowed the cancellation instead of propagating it"

    assert proc.killed, "worker survived cancellation with an unread reply pending"
    assert interp._process is None, (
        "the next execute() would reuse a stream holding the cancelled call's reply"
    )


@pytest.mark.asyncio
async def test_cancelled_during_startup_resets_worker():
    """Cancelling while the handshake is pending must not orphan the child.

    _start() has spawned the process but not yet returned it, so if the
    cancellation escapes without a kill the child is unreachable from anywhere.
    """
    interp = code_interpreter.CodeInterpreter(timeout=30.0)
    spawned = {}

    async def fake_start():
        proc = _FakeProcess([])
        spawned["proc"] = proc
        interp._process = proc
        try:
            await asyncio.Event().wait()  # park, as the real handshake would
        except asyncio.CancelledError:
            await interp._kill()
            raise

    interp._start = fake_start

    task = asyncio.create_task(interp.execute("x"))
    await asyncio.sleep(0.05)
    task.cancel()

    cancelled = False
    try:
        await task
    except asyncio.CancelledError:
        cancelled = True
    assert cancelled
    assert spawned["proc"].killed, "child spawned during startup was orphaned"
    assert interp._process is None


@pytest.mark.asyncio
async def test_cancelled_during_drain_resets_worker():
    """Cancelling while flushing the request must reset the worker.

    The request is partially written, so the worker's view of the stream no
    longer matches ours; reusing it would desynchronize the protocol.
    """

    class _ParkingStdin:
        def __init__(self):
            self.written = []

        def write(self, data):
            self.written.append(data)

        async def drain(self):
            await asyncio.Event().wait()  # never completes

        def close(self):
            pass

    interp = code_interpreter.CodeInterpreter(timeout=30.0)
    proc = _FakeProcess([])
    proc.stdin = _ParkingStdin()
    interp._process = proc

    task = asyncio.create_task(interp.execute("y"))
    await asyncio.sleep(0.05)
    task.cancel()

    cancelled = False
    try:
        await task
    except asyncio.CancelledError:
        cancelled = True
    assert cancelled
    assert proc.killed, "worker survived cancellation with a half-written request"
    assert interp._process is None


@pytest.mark.asyncio
async def test_real_oversized_response_is_rejected():
    """A genuine over-limit frame must be reported and reset the worker.

    Drives a real subprocess emitting a single line larger than the configured
    limit, so this exercises asyncio's actual StreamReader behaviour rather than
    a synthetic ValueError.
    """
    payload = 200_000
    child = (
        "import sys;"
        f"sys.stdout.write('A' * {payload} + chr(10));"
        "sys.stdout.flush()"
    )

    interp = code_interpreter.CodeInterpreter(timeout=30.0)
    # A small limit keeps the test fast while exercising the same code path the
    # 64 MiB production value protects.
    interp.STREAM_LIMIT = 64 * 1024

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        child,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        limit=interp.STREAM_LIMIT,
    )
    interp._process = proc
    try:
        with pytest.raises(code_interpreter.CodeInterpreterError) as excinfo:
            await interp.execute("irrelevant")
        message = str(excinfo.value)
        assert "larger than" in message, message
        assert "reset" in message, message
        assert interp._process is None, "oversized frame left the worker attached"
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


@pytest.mark.asyncio
async def test_real_response_under_limit_is_returned():
    """Control for the test above: a large-but-permitted frame still works.

    The child builds the payload itself; embedding 100 KB in the command line
    exceeds the OS argument limit on Windows.
    """
    child = (
        "import json,sys;"
        "sys.stdout.write(json.dumps("
        "{'stdout':'B'*100000,'stderr':'','result':None,'error':None}"
        ") + chr(10));"
        "sys.stdout.flush()"
    )

    interp = code_interpreter.CodeInterpreter(timeout=30.0)
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        child,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        limit=interp.STREAM_LIMIT,
    )
    interp._process = proc
    try:
        result = await interp.execute("irrelevant")
        assert len(result.stdout) == 100_000, len(result.stdout)
        assert result.stdout.startswith("B")
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


def test_search_files_tolerates_unusable_patterns(tmp_path):
    """Model-supplied glob patterns must not raise out of the tool.

    Path.glob rejects an empty pattern, a malformed '***', and absolute paths.
    The pattern comes straight from the agent, so these must read as "no
    matches" rather than crashing the call.
    """
    (tmp_path / "a.txt").write_text("x")
    sandbox = Sandbox(str(tmp_path))

    # Pattern-syntax errors: these raise on every platform, so the guard around
    # Path.glob is provably load-bearing rather than decorative.
    for pattern in ("", "***"):
        with pytest.raises(ValueError):
            list(tmp_path.glob(pattern))
        assert sandbox.search_files(pattern) == [], f"pattern {pattern!r} leaked"

    # Whether a given string is "absolute" is platform-dependent -- a Windows
    # drive path is just a relative name containing backslashes on POSIX -- so
    # only require that the tool never raises and never returns a match.
    for pattern in ("/etc/passwd", "C:\\Windows\\win.ini", "[", "a[b", "../*"):
        assert sandbox.search_files(pattern) == [], f"pattern {pattern!r} leaked"

    # A valid pattern still works.
    assert sandbox.search_files("*.txt") == ["a.txt"]


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


@pytest_asyncio.fixture
async def sandbox_client_with_secret(tmp_path, monkeypatch):
    """A session whose worker was started *after* a unique secret was exported.

    The secret must be in the parent environment before the worker is spawned,
    otherwise the probe would pass for the wrong reason.
    """
    secret_name = "SANDBOX_PARENT_SECRET_PROBE"
    secret_value = f"parent-secret-{uuid.uuid4().hex}"
    monkeypatch.setenv(secret_name, secret_value)

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
            # Force worker startup now, so it inherits (or does not inherit)
            # the secret exported above.
            await client.call_tool("code_interpreter", {"code": "1"})
            yield SimpleNamespace(client=client, secret=(secret_name, secret_value))
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
    if value not in (repr("REACHABLE"), repr("ABSENT")):
        pytest.fail(
            "probe returned an unexpected value, so the harness is not measuring "
            f"what it claims. got {value!r}, stdout={sc.get('stdout')!r}"
        )
    return "REACHABLE" if value == repr("REACHABLE") else "ABSENT"


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

    Asserts on the *effect* (bytes retrieved), not on whether an API exists.
    Only the specific errors a confining policy would raise are treated as
    ABSENT; anything else propagates and fails the test, so a broken probe is
    never mistaken for confinement.
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
        # ImportError/AttributeError: the loader was removed from the surface.
        # PermissionError/OSError: a policy refused the read.
        "except (ImportError, AttributeError, PermissionError, OSError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record("host files outside the session directory", outcome, "read of a sentinel file")


@pytest.mark.asyncio
async def test_parent_environment_secret_not_visible(sandbox_client_with_secret):
    """A secret exported to the parent must not be visible to agent code.

    Presence of *some* environment is expected and is not a failure: the worker
    is deliberately given PATH and a few operational variables.  What must not
    happen is the parent's own environment reaching agent code, so this looks
    for a unique sentinel exported before the worker started.
    """
    secret_name, secret_value = sandbox_client_with_secret.secret
    outcome = await _capability_probe(
        sandbox_client_with_secret.client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        f"    _v = _F(\"return typeof process==='undefined' ? '' :"
        f" (process.env[{secret_name!r}] || '')\")()\n"
        f"    _r = 'REACHABLE' if _v == {secret_value!r} else 'ABSENT'\n"
        "except (ImportError, AttributeError, PermissionError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )
    _record(
        "a secret exported in the parent environment",
        outcome,
        f"{secret_name} readable via process.env",
    )


@pytest.mark.asyncio
async def test_host_filesystem_write_unavailable(sandbox_client, tmp_path_factory):
    """Agent code must not be able to write outside the session via node:fs.

    Performs a harmless, test-owned write into a directory pytest created, then
    checks the host for the effect.  A rejected dynamic import is *not* swallowed
    here: if the import fails unexpectedly the probe returns something the
    harness does not recognise and the test fails, rather than silently counting
    as confinement.
    """
    target = tmp_path_factory.mktemp("fs_probe") / "written_by_agent.txt"

    js_src = (
        "return import('node:fs').then(m => {"
        f"  m.writeFileSync({json.dumps(str(target))}, 'FS_WRITE_MARKER');"
        "  return 'REACHABLE';"
        "})"
    )
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        f"    _fn = _F({js_src!r})\n"
        "    _r = await _fn()\n"
        "except (ImportError, AttributeError, PermissionError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )

    if outcome == "REACHABLE":
        assert target.exists(), (
            "probe reported a successful write but no host file appeared; "
            "the probe is not measuring what it claims"
        )
        assert "FS_WRITE_MARKER" in target.read_text()
    else:
        assert not target.exists(), "probe reported ABSENT but the host file was written"

    _record("host filesystem writes via node:fs", outcome, "writeFileSync to a test-owned path")


@pytest.mark.asyncio
async def test_process_execution_unavailable(sandbox_client, tmp_path_factory):
    """Agent code must not be able to execute a process.

    Runs a harmless, test-owned command whose only effect is to create a file in
    a directory pytest created, then checks the host for that file.  Nothing is
    downloaded, no network is used, and no state outside that temp directory is
    touched.
    """
    marker = tmp_path_factory.mktemp("proc_probe") / "spawned.txt"

    # A trivial node one-liner: write a marker file and exit.
    inner = f"require('fs').writeFileSync({json.dumps(str(marker))}, 'SPAWN_MARKER')"
    js_src = (
        "return import('node:child_process').then(m => {"
        f"  m.execFileSync(process.execPath, ['-e', {json.dumps(inner)}]);"
        "  return 'REACHABLE';"
        "})"
    )
    outcome = await _capability_probe(
        sandbox_client,
        "try:\n"
        "    import pyodide_js\n"
        "    _F = pyodide_js._api.loadBinaryFile.constructor.constructor\n"
        f"    _fn = _F({js_src!r})\n"
        "    _r = await _fn()\n"
        "except (ImportError, AttributeError, PermissionError):\n"
        "    _r = 'ABSENT'\n"
        "_r",
    )

    if outcome == "REACHABLE":
        assert marker.exists(), (
            "probe reported successful execution but no host file appeared; "
            "the probe is not measuring what it claims"
        )
    else:
        assert not marker.exists(), "probe reported ABSENT but the command ran"

    _record(
        "process execution via node:child_process",
        outcome,
        "execFileSync of a node one-liner",
    )
