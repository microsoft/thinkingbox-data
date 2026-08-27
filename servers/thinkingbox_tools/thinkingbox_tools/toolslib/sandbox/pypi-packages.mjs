// Pure-Python wheels fetched from PyPI.  These are NOT in pyodide's package
// lock, so pyodide.loadPackagesFromImports() cannot auto-load them — they
// must be installed via micropip.  At `npm install` time, scripts/download-wheels.mjs
// downloads each into ./wheels/, and the worker installs from local file://
// URLs to avoid hitting PyPI on every worker startup.  Anything that can't
// be vendored (e.g. no pure-Python wheel published) falls back to a bare
// package name and micropip fetches it at runtime.
export const PYPI_PACKAGES = [
    "openpyxl",
    "xlsxwriter",
    "markdownify",
    "mammoth",
    "pypdf",
    "pdfminer.six",
    "tabulate",
    "plotly",
    "python-docx",
    "python-pptx",
    "reportlab",
];
