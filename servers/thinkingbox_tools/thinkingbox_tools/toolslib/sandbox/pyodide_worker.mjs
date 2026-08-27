/**
 * Pyodide worker — long-lived Node.js process that hosts a Pyodide (CPython-in-WASM)
 * interpreter.  The parent process communicates over stdin/stdout using a simple
 * newline-delimited JSON protocol:
 *
 *   stdin  → { "code": "<python source>" }
 *   stdout ← { "stdout": "...", "stderr": "...", "result": "..." | null, "error": "..." | null }
 *
 * A single { "ready": true } line is written to stdout once Pyodide has finished
 * loading and is ready to accept requests.
 *
 * Diagnostic / startup messages are written to stderr so they never mix with the
 * stdout protocol.
 *
 * Run from the toolslib/ directory so Node.js can resolve the pyodide package:
 *   node pyodide_worker.mjs
 */

import { loadPyodide } from "pyodide";
import { createInterface } from "readline";
import { readdir } from "node:fs/promises";
import { lstatSync, statSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import { PYPI_PACKAGES } from "./pypi-packages.mjs";

// Pyodide and micropip log package-loading progress to Python's sys.stdout
// (e.g. micropip.install internally calls pyodide.loadPackage for transitive
// deps from the lock, which prints "Loading X, Y" / "Loaded X, Y" messages).
// Those would land on Node's stdout and corrupt our JSON protocol, so route
// Python-level output and JS-level console output to stderr instead.  The
// worker uses process.stdout.write directly for protocol frames, which is
// unaffected.  User-code stdout/stderr is captured separately via StringIO
// inside _execute (see below).
const _toStderr = (msg) => process.stderr.write(msg + "\n");
console.log = (...args) => _toStderr(args.join(" "));
console.info = console.log;
console.warn = console.log;

// Parse optional --workspace <path> argument
const workspaceIdx = process.argv.indexOf("--workspace");
const workspacePath = workspaceIdx !== -1 ? process.argv[workspaceIdx + 1] : null;

process.stderr.write("[pyodide_worker] Loading Pyodide...\n");

const pyodide = await loadPyodide({
    stdout: _toStderr,
    stderr: _toStderr,
});

// Packages bundled in pyodide-lock.json — loaded directly as pyodide-built wheels.
const BUNDLED_PACKAGES = [
    "numpy",
    "pandas",
    "micropip",
    "beautifulsoup4",
    "jinja2",
    "sympy",
    "altair",
    "mpmath",
    "lxml",
    "pillow",
];

process.stderr.write("[pyodide_worker] Loading bundled packages...\n");
await pyodide.loadPackage(BUNDLED_PACKAGES, {
    messageCallback: (msg) => process.stderr.write(msg + "\n"),
    errorCallback: (err) => process.stderr.write(err + "\n"),
});

// Resolve each PyPI package to a local wheel (file:// URL) when one was
// vendored by `npm install` into ./wheels/ — avoids hitting PyPI on every
// worker startup.  Anything without a local wheel falls back to a bare
// package name, which micropip resolves via PyPI or via pyodide's own
// bundled wheel set (e.g. reportlab).
const wheelsDir = new URL("./wheels/", import.meta.url);
const normalizePkg = (s) => s.toLowerCase().replace(/[-._]/g, "_");
let localWheels = [];
try {
    localWheels = await readdir(wheelsDir);
} catch {
    process.stderr.write("[pyodide_worker] No local wheels/ directory — micropip will fetch from PyPI\n");
}
const installSpecs = PYPI_PACKAGES.map((pkg) => {
    const target = normalizePkg(pkg);
    // PEP 427 wheel filename: {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    // Compare the normalized distribution segment, not a normalized prefix —
    // normalizePkg(f) rewrites the "-" separators to "_", so a "-"-suffixed
    // prefix could never match.
    const match = localWheels.find((f) => {
        if (!f.endsWith(".whl")) return false;
        const dist = f.split("-")[0];
        return normalizePkg(dist) === target;
    });
    return match ? new URL(match, wheelsDir).href : pkg;
});

process.stderr.write("[pyodide_worker] Installing PyPI packages via micropip...\n");
pyodide.globals.set("_pypi_install_specs", installSpecs);
await pyodide.runPythonAsync(`
import micropip
await micropip.install(list(_pypi_install_specs))
`);
process.stderr.write("[pyodide_worker] Packages loaded.\n");

// Install a reusable _execute helper in Pyodide's global namespace.
// The helper:
//   - redirects stdout/stderr to StringIO buffers for the duration of the call
//   - uses the AST trick to capture the value of a trailing expression (Jupyter style)
//   - runs all code in a shared _namespace dict so variables persist across calls
//   - compiles with PyCF_ALLOW_TOP_LEVEL_AWAIT so user code can `await` directly
//     (e.g. `await micropip.install("pkg")`) — Jupyter / IPython %autoawait semantics
//   - always restores real stdout/stderr in the finally block
await pyodide.runPythonAsync(`
import sys, io, traceback, ast, inspect

_namespace = {}
_real_stdout = sys.stdout
_real_stderr = sys.stderr

_TOP_LEVEL_AWAIT = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT

async def _execute(code):
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    sys.stdout = buf_out
    sys.stderr = buf_err

    result = None
    error = None

    try:
        tree = ast.parse(code, filename="<input>")
        # If the last node is a bare expression, split it off so we can eval it
        # and capture its value (like a Jupyter cell last-expression result).
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            stmts = ast.Module(tree.body[:-1], type_ignores=[])
            ast.fix_missing_locations(stmts)
            # PyCF_ALLOW_TOP_LEVEL_AWAIT turns the compiled object into a
            # coroutine when any await/async-for/async-with appears at module
            # scope; eval() of an exec-mode code object returns that coroutine
            # so we can await it.  exec() would silently drop it.
            stmt_code = compile(stmts, "<input>", "exec", flags=_TOP_LEVEL_AWAIT)
            stmt_coro = eval(stmt_code, _namespace)
            if inspect.iscoroutine(stmt_coro):
                await stmt_coro

            expr_node = ast.Expression(tree.body[-1].value)
            ast.fix_missing_locations(expr_node)
            expr_code = compile(expr_node, "<input>", "eval", flags=_TOP_LEVEL_AWAIT)
            value = eval(expr_code, _namespace)
            if inspect.iscoroutine(value):
                value = await value
            result = value
        else:
            full_code = compile(tree, "<input>", "exec", flags=_TOP_LEVEL_AWAIT)
            full_coro = eval(full_code, _namespace)
            if inspect.iscoroutine(full_coro):
                await full_coro
    except BaseException:
        error = traceback.format_exc()
    finally:
        sys.stdout = _real_stdout
        sys.stderr = _real_stderr

    return (
        buf_out.getvalue(),
        buf_err.getvalue(),
        repr(result) if result is not None else None,
        error,
    )
`);

if (workspacePath) {
    process.stderr.write(`[pyodide_worker] Mounting workspace: ${workspacePath}\n`);
    pyodide.FS.mkdir("/workspace");
    // NODEFS mounts the per-session directory created by mcp_sandbox's
    // __reserved__init.  That directory contains symlinks pointing at the
    // source workspace; reads follow the symlinks transparently, writes are
    // intercepted below to materialize a private copy first.
    pyodide.FS.mount(pyodide.FS.filesystems.NODEFS, { root: workspacePath }, "/workspace");

    // Copy-on-write at the NODEFS layer.  The mount points at a directory of
    // symlinks; if we let Emscripten's path resolver see them as symlinks it
    // would try to FS.readlink and follow the absolute target out of the
    // /workspace/ mount (failing with ENOENT).  Instead we make symlinks look
    // like regular files to Emscripten, then rely on host-level fs.openSync
    // to follow them for reads.  For writes we replace the symlink with a
    // private copy in the session directory before delegating to the real
    // open, so the source file is never mutated.  This catches every caller —
    // builtins.open, os.open, io.FileIO, mmap, sqlite3, numpy — because they
    // all bottom out in NODEFS.
    const NODEFS = pyodide.FS.filesystems.NODEFS;

    const _origLookup = NODEFS.node_ops.lookup;
    NODEFS.node_ops.lookup = function (parent, name) {
        const node = _origLookup(parent, name);
        try {
            const lst = lstatSync(NODEFS.realPath(node));
            if (lst.isSymbolicLink()) {
                const target = statSync(NODEFS.realPath(node));
                node.mode = (node.mode & 0o7777) | (target.mode & 0o170000);
            }
        } catch {}
        return node;
    };

    const _origGetattr = NODEFS.node_ops.getattr;
    NODEFS.node_ops.getattr = function (node) {
        const attr = _origGetattr(node);
        try {
            const path = NODEFS.realPath(node);
            if (lstatSync(path).isSymbolicLink()) {
                const target = statSync(path);
                attr.mode = (attr.mode & 0o7777) | (target.mode & 0o170000);
                attr.size = target.size;
                attr.blocks = Math.ceil(target.size / (attr.blksize || 4096));
                attr.atime = target.atime;
                attr.mtime = target.mtime;
                attr.ctime = target.ctime;
            }
        } catch {}
        return attr;
    };

    const materializeSymlink = (path, preserveContent) => {
        if (preserveContent) {
            const data = readFileSync(path); // follows symlink → source bytes
            unlinkSync(path);
            writeFileSync(path, data);
        } else {
            // O_TRUNC path: caller is about to discard the contents anyway, so
            // skip copying the source bytes — but still leave a real, empty
            // file at the path.  Otherwise `os.open(path, O_WRONLY | O_TRUNC)`
            // (no O_CREAT) would land on a missing host file and fail with
            // ENOENT, even though the symlink looked like a regular file
            // before the open() call.
            unlinkSync(path);
            writeFileSync(path, "");
        }
    };

    const _origStreamOpen = NODEFS.stream_ops.open;
    NODEFS.stream_ops.open = function (stream) {
        const O_ACCMODE = 3;
        const O_TRUNC = 0o1000;
        if ((stream.flags & O_ACCMODE) !== 0) {
            const path = NODEFS.realPath(stream.node);
            let lst;
            try { lst = lstatSync(path); } catch {}
            if (lst && lst.isSymbolicLink()) {
                materializeSymlink(path, (stream.flags & O_TRUNC) === 0);
            }
        }
        return _origStreamOpen(stream);
    };

    const _origSetattr = NODEFS.node_ops.setattr;
    NODEFS.node_ops.setattr = function (node, attr) {
        const path = NODEFS.realPath(node);
        let lst;
        try { lst = lstatSync(path); } catch {}
        if (lst && lst.isSymbolicLink()) {
            materializeSymlink(path, true);
        }
        return _origSetattr(node, attr);
    };

    // Block user code from creating symlinks inside /workspace.  Seeded
    // symlinks (placed by mcp_sandbox.__reserved__init before this mount)
    // are unaffected — they were materialized on the host fs before NODEFS
    // wrapped them, and this hook only fires for in-sandbox symlinkat calls.
    // Without this, user code could do os.symlink("/etc/passwd",
    // "/workspace/x") and then read it transparently via readFileSync's
    // built-in symlink following.
    NODEFS.node_ops.symlink = function () {
        throw new pyodide.FS.ErrnoError(pyodide.ERRNO_CODES.EPERM);
    };

    process.stderr.write("[pyodide_worker] Workspace mounted at /workspace\n");
}

process.stderr.write("[pyodide_worker] Ready.\n");

// Signal readiness to the parent process over stdout.
process.stdout.write(JSON.stringify({ ready: true }) + "\n");

// Process requests one at a time (sequential request/response).
const rl = createInterface({ input: process.stdin, terminal: false });

for await (const line of rl) {
    if (!line.trim()) continue;

    let request;
    try {
        request = JSON.parse(line);
    } catch (e) {
        process.stdout.write(
            JSON.stringify({ stdout: "", stderr: "", result: null, error: `invalid_json: ${e.message}` }) + "\n"
        );
        continue;
    }

    try {
        // Auto-load any pyodide-distributed packages referenced by the user's
        // imports but not in the eager preload set (e.g. matplotlib, scipy).
        // No-op for already-loaded packages.  Pure-Python PyPI packages must
        // still be listed in PYPI_PACKAGES (or installed via micropip in user
        // code) since loadPackagesFromImports only resolves pyodide's lock.
        await pyodide.loadPackagesFromImports(request.code, {
            messageCallback: _toStderr,
            errorCallback: _toStderr,
        });

        pyodide.globals.set("_user_code", request.code);
        // _execute is async — runPythonAsync awaits the returned coroutine.
        const pyResult = await pyodide.runPythonAsync("await _execute(_user_code)");
        const [stdout, stderr, result, error] = pyResult.toJs({ depth: -1 });
        pyResult.destroy();

        process.stdout.write(
            JSON.stringify({
                stdout: stdout ?? "",
                stderr: stderr ?? "",
                result: result ?? null,
                error: error ?? null,
            }) + "\n"
        );
    } catch (e) {
        process.stdout.write(
            JSON.stringify({
                stdout: "",
                stderr: "",
                result: null,
                error: `worker_error: ${e.message}`,
            }) + "\n"
        );
    }
}
