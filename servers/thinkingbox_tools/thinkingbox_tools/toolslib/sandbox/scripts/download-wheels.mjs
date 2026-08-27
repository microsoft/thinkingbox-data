#!/usr/bin/env node
// Vendors pure-Python wheels for the PyPI packages listed in pypi-packages.mjs
// into ../wheels/, so the pyodide worker can install them from local file://
// URLs instead of fetching from PyPI on every startup.
//
// Runs automatically via `npm install` (see package.json "postinstall").
// Idempotent: existing wheel files are kept.  To force a refresh, delete
// the wheels/ directory and re-run `npm install`.
//
// Packages without a pure-Python (`*-none-any.whl`) wheel on PyPI are skipped
// with a warning; the worker falls back to micropip at runtime for those
// (which works because micropip resolves them via pyodide's own bundle when
// available, e.g. reportlab).

import { mkdir, writeFile, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { PYPI_PACKAGES } from "../pypi-packages.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const wheelsDir = join(__dirname, "..", "wheels");

await mkdir(wheelsDir, { recursive: true });

const PURE_PYTHON_WHEEL = /-py[23](\.py3)?-none-any\.whl$/;

async function downloadOne(name) {
    const res = await fetch(`https://pypi.org/pypi/${encodeURIComponent(name)}/json`);
    if (!res.ok) {
        console.warn(`[download-wheels] PyPI returned ${res.status} for ${name} — skipping`);
        return;
    }
    const data = await res.json();
    const version = data.info.version;
    const wheel = (data.releases[version] || []).find(
        (f) => f.packagetype === "bdist_wheel" && PURE_PYTHON_WHEEL.test(f.filename),
    );
    if (!wheel) {
        console.log(`[download-wheels] No pure-Python wheel for ${name} ${version} — leaving to runtime`);
        return;
    }
    const dest = join(wheelsDir, wheel.filename);
    try {
        await access(dest);
        console.log(`[download-wheels] Cached: ${wheel.filename}`);
        return;
    } catch {
        // not present — download below
    }
    console.log(`[download-wheels] Downloading: ${wheel.filename}`);
    const wRes = await fetch(wheel.url);
    if (!wRes.ok) {
        console.warn(`[download-wheels] Download failed (${wRes.status}) for ${wheel.url} — skipping`);
        return;
    }
    await writeFile(dest, Buffer.from(await wRes.arrayBuffer()));
}

await Promise.all(
    PYPI_PACKAGES.map((name) =>
        // A network failure (offline, blocked host, TLS error) rejects fetch()
        // rather than returning a non-ok response.  Without this catch the
        // rejection propagates out of Promise.all and fails `npm install`
        // outright, instead of degrading to the documented behavior: skip the
        // wheel and let micropip fetch it at worker startup.
        downloadOne(name).catch((err) => {
            console.warn(`[download-wheels] ${name}: ${err.message} — leaving to runtime`);
        }),
    ),
);
console.log("[download-wheels] Done.");
