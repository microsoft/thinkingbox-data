# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Validate domain: and eval: tags in scenario YAML files.

USE CASE
--------
Fast, file-scoped validation of scenario YAML files — suitable for use as a
pre-commit hook. Operates directly on raw YAML text without loading the
ThinkingBox hydrator, so it runs quickly on individual staged files.

Checks that any domain: or eval: tag present in a scenario YAML uses a
recognised enum value. Missing tags are allowed (not all scenarios need to
appear on the Leaderboard), but any tag that IS present must use a value
from the enumerated list.

Valid values are derived directly from the Domain and Eval enums in
AI.ThinkingBox/thinkingbox/common/tag_types.py (installed as a package
dependency), so this script stays in sync with the source of truth automatically.

See also: validate_tags.py — the complementary tool for full-stack validation
of test-case Python files across an entire dataset, including tag coverage
reporting, hydration checks, and distribution statistics.

Usage:
    python validate_scenario_tags.py path/to/scenario.yaml [...]
    python validate_scenario_tags.py dataset/scenario/*.yaml

Exits non-zero if any file contains an unrecognised domain: or eval: value.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from thinkingbox.common.tag_types import Domain, Eval

_VALID_DOMAINS = {d.value for d in Domain}
_VALID_EVALS = {e.value for e in Eval}

_TAG_RE = re.compile(r"\btags:\s*\[([^\]]*)\]")
_DOMAIN_RE = re.compile(r"\bdomain:(\S+)")
_EVAL_RE = re.compile(r"\beval:(\S+)")


def _strip_trailing_comma(value: str) -> str:
    return value.rstrip(",")


def validate_file(path: Path) -> list[str]:
    """Return a list of error strings for *path* (empty if valid)."""
    text = path.read_text()
    errors: list[str] = []

    m = _TAG_RE.search(text)
    if m is None:
        return errors  # No tags: line — nothing to validate

    tags_content = m.group(1)

    domain_matches = list(_DOMAIN_RE.finditer(tags_content))
    for dm in domain_matches:
        domain = _strip_trailing_comma(dm.group(1))
        if domain not in _VALID_DOMAINS:
            errors.append(f"unrecognised domain value {domain!r} (valid: {sorted(_VALID_DOMAINS)})")
    if len(domain_matches) > 1:
        values = [_strip_trailing_comma(m.group(1)) for m in domain_matches]
        errors.append(f"multiple domain: tags {values!r} — at most one allowed")

    eval_matches = list(_EVAL_RE.finditer(tags_content))
    for em in eval_matches:
        eval_type = _strip_trailing_comma(em.group(1))
        if eval_type not in _VALID_EVALS:
            errors.append(f"unrecognised eval value {eval_type!r} (valid: {sorted(_VALID_EVALS)})")
    if len(eval_matches) > 1:
        values = [_strip_trailing_comma(m.group(1)) for m in eval_matches]
        errors.append(f"multiple eval: tags {values!r} — at most one allowed")

    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("validate_scenario_tags.py: no files provided", file=sys.stderr)
        return 1

    failed = 0
    for arg in argv:
        path = Path(arg)
        errors = validate_file(path)
        if errors:
            for err in errors:
                print(f"{path}: {err}")
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
