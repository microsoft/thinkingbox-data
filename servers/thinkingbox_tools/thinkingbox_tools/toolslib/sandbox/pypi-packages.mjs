// Pure-Python wheels fetched from PyPI.  These are NOT in pyodide's package
// lock, so pyodide.loadPackagesFromImports() cannot auto-load them — they
// must be installed via micropip.  At `npm install` time, scripts/download-wheels.mjs
// downloads each into ./wheels/, and the worker installs from local file://
// URLs to avoid hitting PyPI on every worker startup.
//
// Each entry pins the exact version, wheel filename and SHA-256 from PyPI's
// metadata.  Pinning matters in two places:
//
//   - download-wheels.mjs fetches that exact release rather than whatever is
//     current, so `npm install` is reproducible and the digest is meaningful.
//   - pyodide_worker.mjs installs only a file whose name matches `filename`
//     exactly.  Matching on the distribution name alone would let any file in
//     wheels/ named e.g. "openpyxl-0.0.1-py3-none-any.whl" be installed
//     instead, since readdir() order decides the winner.
//
// A package with no local wheel falls back to the pinned `name==version`
// spec, so micropip resolves a known version rather than "latest".
//
// To refresh: update version, filename and sha256 together from
// https://pypi.org/pypi/<name>/json — never edit one without the others.
export const PYPI_PACKAGES = [
    {
        name: "openpyxl",
        version: "3.1.5",
        filename: "openpyxl-3.1.5-py2.py3-none-any.whl",
        sha256: "5282c12b107bffeef825f4617dc029afaf41d0ea60823bbb665ef3079dc79de2",
    },
    {
        name: "xlsxwriter",
        version: "3.2.9",
        filename: "xlsxwriter-3.2.9-py3-none-any.whl",
        sha256: "9a5db42bc5dff014806c58a20b9eae7322a134abb6fce3c92c181bfb275ec5b3",
    },
    {
        name: "markdownify",
        version: "1.2.3",
        filename: "markdownify-1.2.3-py3-none-any.whl",
        sha256: "a189a0bedfd14009030fde5f85bb6f77c56897cb839b5c25315dd7d4e3e290ba",
    },
    {
        name: "mammoth",
        version: "1.12.1",
        filename: "mammoth-1.12.1-py2.py3-none-any.whl",
        sha256: "2af047e3e796faa25740112310ddf11f8de2a24c96dc57de3c87dfd7cb6543b3",
    },
    {
        name: "pypdf",
        version: "6.16.2",
        filename: "pypdf-6.16.2-py3-none-any.whl",
        sha256: "c8b09a59399062fb45a1b8156c18a787a10a3dae03ac9674397a226712c94604",
    },
    {
        name: "pdfminer.six",
        version: "20260107",
        filename: "pdfminer_six-20260107-py3-none-any.whl",
        sha256: "366585ba97e80dffa8f00cebe303d2f381884d8637af4ce422f1df3ef38111a9",
    },
    {
        name: "tabulate",
        version: "0.10.0",
        filename: "tabulate-0.10.0-py3-none-any.whl",
        sha256: "f0b0622e567335c8fabaaa659f1b33bcb6ddfe2e496071b743aa113f8774f2d3",
    },
    {
        name: "plotly",
        version: "7.0.0",
        filename: "plotly-7.0.0-py3-none-any.whl",
        sha256: "78cbf7bd06d1b05bb3b8ec1b709864695229b55151b6f7530fbf55517ead6fdd",
    },
    {
        name: "python-docx",
        version: "1.2.0",
        filename: "python_docx-1.2.0-py3-none-any.whl",
        sha256: "3fd478f3250fbbbfd3b94fe1e985955737c145627498896a8a6bf81f4baf66c7",
    },
    {
        name: "python-pptx",
        version: "1.0.2",
        filename: "python_pptx-1.0.2-py3-none-any.whl",
        sha256: "160838e0b8565a8b1f67947675886e9fea18aa5e795db7ae531606d68e785cba",
    },
    {
        name: "reportlab",
        version: "5.0.1",
        filename: "reportlab-5.0.1-py3-none-any.whl",
        sha256: "1c36e6bb0e71780c72331eba60da7f602e8d4389a8723825af71342e49d791e8",
    },
];
