# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import shutil
import tempfile
import traceback
from typing import Annotated, Literal, Union

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from thinkingbox_tools.toolslib.sandbox.code_interpreter import (
    CodeInterpreter,
    CodeInterpreterError,
)
from thinkingbox_tools.toolslib.sandbox.sandbox import Sandbox

mcp = FastMCP("sandbox")

_sandbox: Sandbox | None = None
_interpreter: CodeInterpreter | None = None
_session_dir: str | None = (
    None  # per-session copy of workspace_dir, cleaned up on teardown
)


class FilesResult(BaseModel):
    status: Literal["ok"] = "ok"
    files: list[str]


class ExecutionResult(BaseModel):
    status: Literal["ok"] = "ok"
    stdout: str
    stderr: str
    result: str | None
    error: str | None


class ErrorResult(BaseModel):
    status: Literal["error"] = "error"
    message: str


def _symlink_or_copy(src: str, dst: str) -> None:
    """Symlink dst → src; fall back to a real copy if symlinks aren't supported."""
    try:
        os.symlink(os.path.abspath(src), dst)
    except OSError:
        shutil.copy2(src, dst)


@mcp.tool(name="__reserved__init")
async def initialize(config: dict):
    global _sandbox, _interpreter, _session_dir

    workspace_dir = os.path.expanduser(os.path.expandvars(config.get("workspace_dir", "")))
    timeout = config.get("timeout", 30.0)

    # Populate a fresh temp directory with symlinks to the workspace files.
    # Symlinks don't duplicate bytes, so init cost is proportional to the number
    # of files rather than their size.  Copy-on-write is enforced at the NODEFS
    # layer inside the Pyodide worker (see pyodide_worker.mjs): when a symlink
    # is opened for write, the worker replaces it with a private copy in the
    # session directory before the write proceeds, leaving the source file
    # untouched.  New files created by the agent are regular files from the
    # start and need no special handling.  Falls back to a real copy if the
    # filesystem doesn't support symlinks.
    if _session_dir is not None:
        shutil.rmtree(_session_dir, ignore_errors=True)
    _session_dir = tempfile.mkdtemp(prefix="sandbox_session_")
    if workspace_dir and os.path.isdir(workspace_dir):
        shutil.copytree(
            workspace_dir, _session_dir, copy_function=_symlink_or_copy, dirs_exist_ok=True
        )

    _sandbox = Sandbox(_session_dir)
    if _interpreter is not None:
        await _interpreter.close()
    _interpreter = CodeInterpreter(timeout=timeout, workspace_dir=_session_dir)
    return {}


@mcp.tool(name="__reserved__teardown")
async def teardown():
    global _sandbox, _interpreter, _session_dir
    if _interpreter is not None:
        await _interpreter.close()
        _interpreter = None
    _sandbox = None
    if _session_dir is not None:
        shutil.rmtree(_session_dir, ignore_errors=True)
        _session_dir = None
    return {}


@mcp.tool(name="__reserved__geteffects")
async def geteffects():
    return {"effects": _interpreter.effects if _interpreter else []}


@mcp.tool(
    name="list_sandbox_files",
    description=(
        "List files in the workspace whose paths start with a given prefix. "
        "The directory separator is /. "
        "Returned paths are relative to the workspace root; prepend /workspace/ to use them in code_interpreter (e.g. 'reports/q1.csv' → open('/workspace/reports/q1.csv'))."
    ),
)
async def list_files(
    prefix: Annotated[
        str,
        Field(
            description="Path prefix to filter by, e.g. 'reports/' or '' for all files"
        ),
    ] = "",
) -> Union[FilesResult, ErrorResult]:
    if _sandbox is None:
        return ErrorResult(message="not initialized")
    return FilesResult(files=_sandbox.list_files(prefix))


@mcp.tool(
    name="search_sandbox_files",
    description=(
        "Find files in the workspace whose paths match a wildcard pattern. "
        "Returned paths are relative to the workspace root; prepend /workspace/ to use them in code_interpreter (e.g. 'reports/q1.csv' → open('/workspace/reports/q1.csv'))."
    ),
)
async def search_files(
    pattern: Annotated[
        str,
        Field(
            description="Glob pattern, e.g. '*.csv', 'reports/**/*.pdf', or '**/*.xlsx'"
        ),
    ],
) -> Union[FilesResult, ErrorResult]:
    if _sandbox is None:
        return ErrorResult(message="not initialized")
    return FilesResult(files=_sandbox.search_files(pattern))


@mcp.tool(
    name="code_interpreter",
    description=(
        "Execute Python code in a sandboxed Pyodide (CPython-in-WebAssembly) interpreter. "
        "Workspace files are accessible at /workspace/<path> using standard Python file I/O. "
        "Pre-installed: numpy, pandas, beautifulsoup4, jinja2, sympy, altair, mpmath, lxml, "
        "Pillow, openpyxl, xlsxwriter, markdownify, mammoth, pypdf, pdfminer.six, tabulate, "
        "plotly, python-docx, python-pptx, reportlab. "
        "Use micropip.install() to add other pure-Python packages. "
        "The interpreter is stateful: variables and imports persist across calls."
    ),
)
async def execute_python(
    code: Annotated[str, Field(description="Python source code to execute")],
) -> Union[ExecutionResult, ErrorResult]:
    if _interpreter is None:
        return ErrorResult(message="not initialized")
    try:
        res = await _interpreter.execute(code)
        return ExecutionResult(
            stdout=res.stdout,
            stderr=res.stderr,
            result=res.result,
            error=res.error,
        )
    except CodeInterpreterError as e:
        return ErrorResult(message=str(e))
    except Exception:
        traceback.print_exc()
        return ErrorResult(message="Internal error")


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
