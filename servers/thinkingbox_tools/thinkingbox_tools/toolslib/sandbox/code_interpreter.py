# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

# Opt-in required to run the worker unconfined.  Pyodide is not a privilege
# boundary (see docs/sandbox_code_interpreter.md "Threat model"), so the default
# is to refuse to start rather than to silently execute agent code with the
# permissions of the MCP server process.
UNCONFINED_OPT_IN_ENV = "THINKINGBOX_SANDBOX_ALLOW_UNCONFINED"

# Passed through to the worker when present.  Everything else in the parent
# environment is withheld: the worker inherits the MCP server's environment
# otherwise, and agent code can read all of it.  This narrows the blast radius
# of an escape; it is NOT isolation, and does not stop an escape from happening.
_ENV_ALLOWLIST = (
    "PATH",  # required to locate the node binary
    "SystemRoot",  # Windows: required by the CRT / winsock
    "SystemDrive",
    "COMSPEC",
    "NUMBER_OF_PROCESSORS",  # libuv threadpool sizing
    "LANG",
    "LC_ALL",
    "TZ",
)


def _minimal_env(worker_tmp: str | None = None) -> dict[str, str]:
    """Build the worker environment from an allowlist.

    Defense-in-depth only.  A process that escapes Pyodide still runs with the
    OS-level privileges of this user; withholding variables merely means the
    escape does not hand over whatever secrets happened to be exported.
    """
    env = {name: os.environ[name] for name in _ENV_ALLOWLIST if name in os.environ}
    # Node reads TMPDIR/TEMP/TMP for os.tmpdir().  Point them at a directory
    # this interpreter owns rather than forwarding the parent's values, so
    # worker scratch files do not land in a shared temp location.  When no
    # directory is supplied the variables are omitted entirely and Node falls
    # back to its platform default.
    if worker_tmp:
        for name in ("TMPDIR", "TEMP", "TMP"):
            env[name] = worker_tmp
    return env


def _unconfined_allowed() -> bool:
    """True when the operator has explicitly opted in to unconfined execution."""
    return os.environ.get(UNCONFINED_OPT_IN_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


class CodeInterpreterError(Exception):
    pass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    result: str | None  # repr() of the last expression, or None
    error: str | None  # formatted traceback, or None


class CodeInterpreter:
    """
    Manages a long-lived Node.js / Pyodide subprocess.

    The subprocess hosts a CPython-in-WASM interpreter and communicates over
    stdin/stdout using a newline-delimited JSON protocol (see pyodide_worker.mjs).

    The interpreter is stateful like a REPL: variables defined in one execute()
    call are visible in subsequent calls.  Call close() (or reinitialize via the
    MCP __reserved__init tool) to get a fresh interpreter.

    Requires Node.js and the pyodide npm package:
        cd thinkingbox_tools/toolslib/sandbox && npm install
    """

    # Pyodide loads the runtime + several dozen wheels on startup. The first run
    # fetches PyPI wheels over the network; subsequent runs use the local cache.
    STARTUP_TIMEOUT = 300.0

    # asyncio's StreamReader defaults to a 64 KiB line limit, and the protocol
    # puts one JSON frame per line.  A single print() of a moderately sized
    # DataFrame exceeds that, and readline() then raises ValueError rather than
    # returning the frame -- so a routine analysis would fail with an opaque
    # error.  Raise the ceiling well above realistic output while still bounding
    # memory for a runaway producer.
    STREAM_LIMIT = 64 * 1024 * 1024

    def __init__(self, timeout: float = 30.0, workspace_dir: str | None = None):
        self.timeout = timeout
        self.workspace_dir = workspace_dir
        self.effects: list[dict] = []
        self._process: asyncio.subprocess.Process | None = None
        self._worker_path = Path(__file__).parent / "pyodide_worker.mjs"
        # Scratch directory handed to the worker as TMPDIR/TEMP/TMP, created on
        # first start and removed on close so worker temp files do not outlive
        # the interpreter or share the host's temp root.
        self._worker_tmp: str | None = None
        # Serializes execute() and close() against the shared worker stdio.
        # The worker speaks a strict request/response protocol on a single
        # stdin/stdout pair, so two concurrent execute() coroutines would
        # interleave writes and race to read each other's response frame.
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(self, code: str) -> ExecutionResult:
        async with self._lock:
            await self._ensure_started()

            request = json.dumps({"code": code}) + "\n"
            self._process.stdin.write(request.encode())
            await self._process.stdin.drain()

            try:
                response_line = await asyncio.wait_for(
                    self._process.stdout.readline(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                await self._kill()
                raise CodeInterpreterError(
                    f"Execution timed out after {self.timeout}s. "
                    "The interpreter has been reset."
                )
            except asyncio.CancelledError:
                # The caller went away (client disconnect, MCP cancellation, an
                # outer wait_for) while the request was in flight.  The worker
                # will still write its reply, and that unread frame would be
                # returned to the *next* execute() as its result -- a silently
                # wrong answer rather than an error.  CancelledError is a
                # BaseException, so nothing upstream catches this for us.
                await self._kill()
                raise
            except (ValueError, asyncio.LimitOverrunError) as exc:
                # readline() raises when a frame exceeds STREAM_LIMIT.  The
                # unread remainder would be parsed as the *next* response, so
                # the worker has to be reset rather than reused.
                await self._kill()
                raise CodeInterpreterError(
                    f"Worker produced a response frame larger than "
                    f"{self.STREAM_LIMIT} bytes ({exc}). The interpreter has "
                    "been reset. Reduce the amount of data printed or returned."
                )

            if not response_line:
                await self._kill()
                raise CodeInterpreterError(
                    "Worker process closed unexpectedly. "
                    "The interpreter has been reset."
                )

            # A frame that is not a JSON object means the stream is no longer in
            # sync with the protocol -- anything still buffered would be read as
            # the next response and silently returned for the wrong call.  Kill
            # the worker so the next execute() starts from a known state.
            try:
                data = json.loads(response_line)
            except ValueError:
                await self._kill()
                raise CodeInterpreterError(
                    "Worker produced a malformed response frame; the protocol "
                    "stream is out of sync. The interpreter has been reset."
                )
            if not isinstance(data, dict):
                await self._kill()
                raise CodeInterpreterError(
                    "Worker produced an unexpected response frame; the protocol "
                    "stream is out of sync. The interpreter has been reset."
                )

            result = ExecutionResult(
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", ""),
                result=data.get("result"),
                error=data.get("error"),
            )

            self.effects.append(
                {"type": "code_execution", "code": code, "result": asdict(result)}
            )
            return result

    async def close(self) -> None:
        """Gracefully stop the worker process."""
        async with self._lock:
            if self._process is None:
                self._cleanup_worker_tmp()
                return
            try:
                self._process.stdin.close()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                await self._kill()
            finally:
                self._process = None
                self._cleanup_worker_tmp()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cleanup_worker_tmp(self) -> None:
        if self._worker_tmp:
            shutil.rmtree(self._worker_tmp, ignore_errors=True)
            self._worker_tmp = None

    async def _ensure_started(self) -> None:
        if self._process is None or self._process.returncode is not None:
            await self._start()

    async def _start(self) -> None:
        # Fail closed.  Pyodide does not confine agent code, so refuse to spawn
        # an unconfined worker unless the operator has explicitly accepted that.
        # A documentation warning is not a control; this is.
        if not _unconfined_allowed():
            raise CodeInterpreterError(
                "Refusing to start the code interpreter: it would run agent-supplied "
                "Python unconfined.\n"
                "Pyodide is NOT a security boundary -- code executed here can reach "
                "the Node host, the host filesystem, process execution and this "
                "process's environment variables.\n"
                "Only enable this where the executed code is trusted -- note "
                "that first-party provenance is not itself trust -- and the "
                "execution context is secret-free, by setting:\n"
                f"  {UNCONFINED_OPT_IN_ENV}=1\n"
                "See docs/sandbox_code_interpreter.md ('Threat model')."
            )

        worker_dir = self._worker_path.parent
        if not self._worker_path.exists():
            raise CodeInterpreterError(
                f"Worker script not found: {self._worker_path}\n"
                f"Run 'npm install' in {worker_dir} first."
            )
        # node_modules is not packaged in the wheel — the sandbox depends on
        # the pyodide npm package, which the user must install once after
        # `pip install` (see docs/sandbox_code_interpreter.md).  Detecting it
        # before spawning lets us surface a precise remediation message
        # instead of a generic "Cannot find package 'pyodide'" from Node.
        if not (worker_dir / "node_modules" / "pyodide").exists():
            raise CodeInterpreterError(
                "Pyodide Node dependency is not installed. Run once after "
                f"`pip install`:\n  cd {worker_dir} && npm install"
            )

        cmd = ["node", str(self._worker_path)]
        if self.workspace_dir:
            cmd += ["--workspace", self.workspace_dir]
        if self._worker_tmp is None:
            self._worker_tmp = tempfile.mkdtemp(prefix="sandbox_worker_tmp_")
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            # Inherit parent stderr. Pyodide + micropip emit substantial
            # diagnostic output during startup and on every loadPackagesFromImports
            # call; piping it without a drain task would eventually block the worker
            # once the kernel pipe buffer (~64KB on Linux) fills.
            stderr=None,
            # Run from the worker's own directory so Node.js can resolve
            # the pyodide package in the sibling node_modules/ folder.
            cwd=str(self._worker_path.parent),
            # Withhold the parent environment (defense-in-depth, not isolation).
            env=_minimal_env(self._worker_tmp),
            # Raise the StreamReader line limit above asyncio's 64 KiB default;
            # response frames carry user stdout and can legitimately be large.
            limit=self.STREAM_LIMIT,
        )

        # Wait for the { "ready": true } handshake before accepting requests.
        try:
            ready_line = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=self.STARTUP_TIMEOUT,
            )
        except asyncio.TimeoutError:
            await self._kill()
            raise CodeInterpreterError(
                f"Worker timed out during startup (>{self.STARTUP_TIMEOUT}s). "
                f"Make sure 'npm install' has been run in {worker_dir}."
            )
        except (ValueError, asyncio.LimitOverrunError) as exc:
            await self._kill()
            raise CodeInterpreterError(
                f"Worker emitted an oversized handshake frame ({exc})."
            )

        if not ready_line:
            await self._kill()
            raise CodeInterpreterError(
                "Worker exited before sending ready signal. "
                "See [pyodide_worker] output above for details."
            )
        # A non-JSON handshake previously raised out of _start() with the child
        # still running, leaking a Pyodide process on every retry.
        try:
            ready = json.loads(ready_line)
        except ValueError:
            await self._kill()
            raise CodeInterpreterError(
                "Worker sent a malformed handshake frame. "
                "See [pyodide_worker] output above for details."
            )
        if not isinstance(ready, dict) or not ready.get("ready"):
            await self._kill()
            raise CodeInterpreterError(f"Unexpected worker handshake: {ready}")

    async def _kill(self) -> None:
        if self._process:
            try:
                self._process.kill()
                await self._process.wait()
            except Exception:
                # Best effort: the worker may already be dead, or reaping it may
                # race with the event loop shutting down.  Either way the process
                # handle is dropped below and the next call spawns a fresh one,
                # so there is nothing useful to recover or report here.
                pass
            finally:
                self._process = None
