#!/usr/bin/env node
// Vendors the exact pinned wheels listed in pypi-packages.mjs into ../wheels/,
// so the pyodide worker can install them from local file:// URLs instead of
// fetching from PyPI on every startup.
//
// Runs automatically via `npm install` (see package.json "postinstall").
// Idempotent: a cached wheel whose SHA-256 matches the pin is kept.
//
// Network failures degrade gracefully -- the wheel is skipped and the worker
// falls back to the pinned `name==version` spec at runtime.  Integrity
// failures do NOT degrade: if a bad file cannot be removed, or PyPI's digest
// disagrees with the pin, the install fails rather than leaving something the
// worker would load.

import { mkdir, writeFile, readFile, rm, rename } from "node:fs/promises";
import { existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { PYPI_PACKAGES } from "../pypi-packages.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
// Overridable only so tests can exercise the integrity paths against a scratch
// directory and a local stub. Production uses the sibling wheels/ dir and PyPI.
const wheelsDir = process.env.THINKINGBOX_WHEELS_DIR || join(__dirname, "..", "wheels");

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");

await mkdir(wheelsDir, { recursive: true });

// Bounded so a stalled connection cannot hang `npm install`; fetch() has no
// default timeout.
const METADATA_TIMEOUT_MS = 30_000;
const DOWNLOAD_TIMEOUT_MS = 120_000;

// Overridable only so the integrity paths can be exercised against a local
// stub in tests.  Production always uses PyPI.
const PYPI_BASE_URL = process.env.THINKINGBOX_PYPI_BASE_URL || "https://pypi.org/pypi";

// Raised for conditions that must abort the install rather than degrade.
class IntegrityError extends Error {}

async function downloadOne(pkg) {
    const { name, version, filename, sha256: expected } = pkg;
    const dest = join(wheelsDir, filename);

    // Re-verify a cached wheel rather than trusting the filename: the cache
    // lives in a working directory that anything on this machine can write to.
    // A wheel that fails the check must be removed -- leaving it in place would
    // mean the check detects a bad wheel and the worker installs it anyway.
    // If it cannot be removed, fail: continuing would leave a known-bad file
    // where the worker will pick it up.
    try {
        const cached = await readFile(dest);
        if (sha256(cached) === expected) {
            console.log(`[download-wheels] Cached: ${filename}`);
            return;
        }
        console.warn(`[download-wheels] Cached ${filename} failed digest check — removing`);
        await rm(dest, { force: true });
    } catch (err) {
        if (err?.code !== "ENOENT") {
            // Unreadable, or the removal above threw.  Try once more and fail
            // loudly if the bad file survives.
            try {
                await rm(dest, { force: true });
            } catch (rmErr) {
                throw new IntegrityError(
                    `Refusing to continue: ${dest} failed its integrity check and could ` +
                        `not be removed (${rmErr.message}). Delete it manually before ` +
                        `re-running, or the worker will install it.`,
                );
            }
        }
    }

    // Guard against a removal that silently did not happen (permissions, a
    // read-only mount, or a file recreated by something else).
    if (existsSync(dest)) {
        throw new IntegrityError(
            `Refusing to continue: ${dest} failed its integrity check and is still ` +
                `present after removal. Delete it manually before re-running.`,
        );
    }

    console.log(`[download-wheels] Downloading: ${filename}`);
    // Resolve the pinned release, not data.info.version: `npm install` must be
    // reproducible, and a digest is only meaningful against a fixed artifact.
    const res = await fetch(`${PYPI_BASE_URL}/${encodeURIComponent(name)}/${encodeURIComponent(version)}/json`, {
        signal: AbortSignal.timeout(METADATA_TIMEOUT_MS),
    });
    if (!res.ok) {
        console.warn(`[download-wheels] PyPI returned ${res.status} for ${name} ${version} — leaving to runtime`);
        return;
    }
    const data = await res.json();
    const wheel = (data.urls || []).find((f) => f.filename === filename);
    if (!wheel) {
        console.warn(`[download-wheels] ${filename} not found in ${name} ${version} — leaving to runtime`);
        return;
    }
    if (wheel.digests?.sha256 !== expected) {
        // PyPI's own digest disagrees with the pin: either the pin is stale or
        // the artifact changed. Either way, do not download it.
        throw new IntegrityError(
            `Refusing to download ${filename}: PyPI reports sha256 ` +
                `${wheel.digests?.sha256}, pinned value is ${expected}. ` +
                `Update pypi-packages.mjs deliberately if this is an intended bump.`,
        );
    }

    const wRes = await fetch(wheel.url, {
        signal: AbortSignal.timeout(DOWNLOAD_TIMEOUT_MS),
    });
    if (!wRes.ok) {
        console.warn(`[download-wheels] Download failed (${wRes.status}) for ${wheel.url} — skipping`);
        return;
    }

    // These wheels are installed into the interpreter, so a corrupted or
    // substituted file is code execution.  Verify the bytes actually received.
    // A mismatch here means the artifact served does not match the pin, which
    // is an integrity failure and not a transport problem -- degrading to a
    // runtime micropip fetch would silently install whatever PyPI serves next
    // instead of surfacing that the pinned artifact could not be obtained.
    const body = Buffer.from(await wRes.arrayBuffer());
    const actual = sha256(body);
    if (actual !== expected) {
        throw new IntegrityError(
            `Downloaded ${filename} does not match its pinned digest ` +
                `(expected ${expected}, got ${actual}). Refusing to install. ` +
                `Update pypi-packages.mjs deliberately if this is an intended bump.`,
        );
    }

    // Write via a temp file and rename so an interrupted install cannot leave a
    // truncated wheel behind.  A truncated file would fail every later digest
    // check, and with PyPI unreachable -- the case this vendoring exists for --
    // `npm install` could never repair it.
    const tmp = `${dest}.${process.pid}.tmp`;
    try {
        await writeFile(tmp, body);
        await rename(tmp, dest);
    } catch (err) {
        await rm(tmp, { force: true }).catch(() => {});
        throw err;
    }
}

const results = await Promise.all(
    PYPI_PACKAGES.map((pkg) =>
        // A network failure (offline, blocked host, TLS error) rejects fetch()
        // rather than returning a non-ok response, and must degrade to the
        // documented behavior: skip the wheel, let micropip fetch the pinned
        // version at worker startup.  An IntegrityError is different in kind --
        // it means a file the worker would load cannot be trusted -- so it is
        // rethrown below and fails the install.
        downloadOne(pkg).then(
            () => null,
            (err) => {
                if (err instanceof IntegrityError) return err;
                console.warn(`[download-wheels] ${pkg.name}: ${err.message} — leaving to runtime`);
                return null;
            },
        ),
    ),
);

const integrityFailures = results.filter(Boolean);
if (integrityFailures.length > 0) {
    for (const err of integrityFailures) {
        console.error(`[download-wheels] INTEGRITY FAILURE: ${err.message}`);
    }
    process.exitCode = 1;
    throw new Error(
        `${integrityFailures.length} wheel(s) failed integrity checks and could not be ` +
            `quarantined. Refusing to complete installation.`,
    );
}
console.log("[download-wheels] Done.");
