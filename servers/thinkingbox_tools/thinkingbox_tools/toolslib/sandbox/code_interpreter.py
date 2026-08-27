# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


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

    def __init__(self, timeout: float = 30.0, workspace_dir: str | None = None):
        self.timeout = timeout
        self.workspace_dir = workspace_dir
        self.effects: list[dict] = []
        self._process: asyncio.subprocess.Process | None = None
        self._worker_path = Path(__file__).parent / "pyodide_worker.mjs"
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

            if not response_line:
                await self._kill()
                raise CodeInterpreterError(
                    "Worker process closed unexpectedly. "
                    "The interpreter has been reset."
                )

            data = json.loads(response_line)
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
                return
            try:
                self._process.stdin.close()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                await self._kill()
            finally:
                self._process = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_started(self) -> None:
        if self._process is None or self._process.returncode is not None:
            await self._start()

    async def _start(self) -> None:
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

        if not ready_line:
            await self._kill()
            raise CodeInterpreterError(
                "Worker exited before sending ready signal. "
                "See [pyodide_worker] output above for details."
            )
        ready = json.loads(ready_line)
        if not ready.get("ready"):
            await self._kill()
            raise CodeInterpreterError(f"Unexpected worker handshake: {ready}")

    async def _kill(self) -> None:
        if self._process:
            try:
                self._process.kill()
                await self._process.wait()
            except Exception:
                pass
            finally:
                self._process = None
