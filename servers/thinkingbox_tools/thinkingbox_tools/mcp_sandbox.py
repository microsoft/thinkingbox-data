# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import shutil
import stat
import sys
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

# SECURITY: Pyodide is NOT a security boundary.  It provides memory safety via
# WASM, but deliberately exposes a Python<->JavaScript FFI, and Python code can
# reach the Node host through it (`import js`, cached JsProxy references, and
# the Function constructor, which evaluates in global scope and therefore
# survives jsglobals restriction or module hiding).  Host filesystem access,
# process execution and environment variables are all reachable.
#
# Run only trusted, first-party agent code here.  Do not route untrusted or
# third-party input to this server until the worker is confined by an OS/
# container boundary.  See docs/sandbox_code_interpreter.md ("Threat model").

mcp = FastMCP("sandbox")

# Win32 IsReparseTagNameSurrogate: bit 29 marks reparse tags that name another
# filesystem location (junctions, symlinks) as opposed to tags describing
# alternate backing storage for the same file (OneDrive placeholders, dedup).
_IO_REPARSE_TAG_NAME_SURROGATE_BIT = 0x20000000

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


def _is_link(path: str) -> bool:
    """True for symlinks and for Windows reparse points that redirect by name.

    ``os.path.islink`` returns False for Windows junctions, so reparse points are
    inspected explicitly.  Only *name surrogates* count: those are the reparse
    tags that name another filesystem location (junctions, symlinks, mount
    points) and are therefore traversal risks.  Non-surrogate reparse points
    describe alternate backing storage for the same file -- OneDrive / Files
    On-Demand placeholders, deduplication, WIM/container mappings -- and must be
    treated as ordinary files, or a user with OneDrive-backed files would have
    their whole workspace rejected.

    This mirrors the Win32 ``IsReparseTagNameSurrogate`` macro, which tests bit
    29 of the tag.  An entry that cannot be inspected is reported as a link so
    callers fail closed.
    """
    try:
        st = os.lstat(path)
    except OSError:
        return True
    if stat.S_ISLNK(st.st_mode):
        return True

    reparse_attr = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if not (getattr(st, "st_file_attributes", 0) & reparse_attr):
        return False

    tag = getattr(st, "st_reparse_tag", 0)
    if not tag:
        # Reparse point whose tag we can't read: fail closed.
        return True
    return bool(tag & _IO_REPARSE_TAG_NAME_SURROGATE_BIT)


def _resolves_inside(path: str, root: str) -> bool:
    """True when ``path`` fully resolves to a location at or under ``root``."""
    try:
        real_root = os.path.realpath(root)
        real_path = os.path.realpath(path)
    except OSError:
        return False
    return real_path == real_root or real_path.startswith(real_root + os.sep)


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
        workspace_root = os.path.abspath(workspace_dir)
        rejected: list[str] = []

        def _seed(src: str, dst: str) -> None:
            # A link in the *source* workspace would otherwise be re-pointed at
            # its own target, and NODEFS reads follow host links transparently —
            # so a link escaping workspace_dir would be readable from inside the
            # sandbox.  In-workspace links are materialized as real copies so
            # legitimate data is preserved without keeping a followable link.
            if _is_link(src):
                if _resolves_inside(src, workspace_root):
                    shutil.copy2(src, dst, follow_symlinks=True)
                else:
                    rejected.append(src)
                return
            _symlink_or_copy(src, dst)

        def _ignore(dirpath: str, names: list[str]) -> set[str]:
            # Linked directories are rejected outright: following them risks both
            # traversal outside the workspace and copytree recursion loops.
            drop = set()
            for name in names:
                entry = os.path.join(dirpath, name)
                if os.path.isdir(entry) and _is_link(entry):
                    rejected.append(entry)
                    drop.add(name)
            return drop

        shutil.copytree(
            workspace_dir,
            _session_dir,
            copy_function=_seed,
            ignore=_ignore,
            dirs_exist_ok=True,
        )
        if rejected:
            print(
                f"[mcp_sandbox] refused to seed {len(rejected)} link(s) that "
                f"escape the workspace: {', '.join(sorted(rejected)[:5])}"
                + (" ..." if len(rejected) > 5 else ""),
                file=sys.stderr,
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
        "Execute Python code in a Pyodide (CPython-in-WebAssembly) interpreter. "
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
