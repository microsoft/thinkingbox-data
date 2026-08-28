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

import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { PYPI_PACKAGES } from "../pypi-packages.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const wheelsDir = join(__dirname, "..", "wheels");

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");

await mkdir(wheelsDir, { recursive: true });

const PURE_PYTHON_WHEEL = /-py[23](\.py3)?-none-any\.whl$/;

// A stalled connection would otherwise hang `npm install` indefinitely, since
// fetch() has no default timeout.  Bounding it lets the script fail fast and
// degrade to a runtime micropip fetch, as documented.
const METADATA_TIMEOUT_MS = 30_000;
const DOWNLOAD_TIMEOUT_MS = 120_000;

async function downloadOne(name) {
    const res = await fetch(`https://pypi.org/pypi/${encodeURIComponent(name)}/json`, {
        signal: AbortSignal.timeout(METADATA_TIMEOUT_MS),
    });
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
    const expected = wheel.digests?.sha256;
    if (!expected) {
        console.warn(`[download-wheels] No sha256 published for ${wheel.filename} — leaving to runtime`);
        return;
    }

    // Re-verify a cached wheel rather than trusting the filename: the cache
    // lives in a working directory that anything on this machine can write to.
    try {
        const cached = await readFile(dest);
        if (sha256(cached) === expected) {
            console.log(`[download-wheels] Cached: ${wheel.filename}`);
            return;
        }
        console.warn(`[download-wheels] Cached ${wheel.filename} failed digest check — refetching`);
    } catch {
        // not present — download below
    }

    console.log(`[download-wheels] Downloading: ${wheel.filename}`);
    const wRes = await fetch(wheel.url, {
        signal: AbortSignal.timeout(DOWNLOAD_TIMEOUT_MS),
    });
    if (!wRes.ok) {
        console.warn(`[download-wheels] Download failed (${wRes.status}) for ${wheel.url} — skipping`);
        return;
    }

    // These wheels are installed into the interpreter, so a corrupted or
    // substituted file is code execution.  PyPI publishes a sha256 in the
    // metadata; refuse to write anything that does not match it.
    const body = Buffer.from(await wRes.arrayBuffer());
    const actual = sha256(body);
    if (actual !== expected) {
        console.warn(
            `[download-wheels] DIGEST MISMATCH for ${wheel.filename} ` +
                `(expected ${expected}, got ${actual}) — refusing to write, leaving to runtime`,
        );
        return;
    }
    await writeFile(dest, body);
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
