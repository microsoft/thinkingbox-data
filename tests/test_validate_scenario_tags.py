# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for scripts/validate_scenario_tags.py."""

import sys
from pathlib import Path

import pytest

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_scenario_tags import validate_file


def yaml_file(tmp_path, content: str) -> Path:
    p = tmp_path / "scenario.yaml"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# No tags — always valid
# ---------------------------------------------------------------------------


def test_no_tags_line_is_valid(tmp_path):
    p = yaml_file(tmp_path, "world_state:\n  foo: bar\nbot_instructions: ''\n")
    assert validate_file(p) == []


# ---------------------------------------------------------------------------
# domain: tag
# ---------------------------------------------------------------------------


def test_valid_domain_passes(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:customer-service]\n")
    assert validate_file(p) == []


def test_invalid_domain_fails(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:foo]\n")
    errors = validate_file(p)
    assert len(errors) == 1
    assert "domain" in errors[0]
    assert "foo" in errors[0]


def test_invalid_domain_caught_when_valid_domain_also_present(tmp_path):
    """Regression: search() stopped at first match; finditer() checks all."""
    p = yaml_file(tmp_path, "tags: [domain:misc, domain:foo]\n")
    errors = validate_file(p)
    assert any("foo" in e for e in errors)


def test_multiple_valid_domains_fail(tmp_path):
    """Two valid domain values are still an error — at most one allowed."""
    p = yaml_file(tmp_path, "tags: [domain:sales, domain:hr]\n")
    errors = validate_file(p)
    assert any("multiple domain" in e for e in errors)


def test_multiple_invalid_domains_all_reported(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:foo, domain:bar]\n")
    errors = validate_file(p)
    assert any("foo" in e for e in errors)
    assert any("bar" in e for e in errors)


# ---------------------------------------------------------------------------
# eval: tag
# ---------------------------------------------------------------------------


def test_valid_eval_passes(tmp_path):
    p = yaml_file(tmp_path, "tags: [eval:orchestration:tool-selection]\n")
    assert validate_file(p) == []


def test_invalid_eval_fails(tmp_path):
    p = yaml_file(tmp_path, "tags: [eval:bar]\n")
    errors = validate_file(p)
    assert len(errors) == 1
    assert "eval" in errors[0]
    assert "bar" in errors[0]


def test_invalid_eval_caught_when_valid_eval_also_present(tmp_path):
    p = yaml_file(tmp_path, "tags: [eval:knowledge-qa:text, eval:bar]\n")
    errors = validate_file(p)
    assert any("bar" in e for e in errors)


def test_all_valid_eval_values_pass(tmp_path):
    valid = [
        "eval:orchestration:tool-selection",
        "eval:knowledge-qa:text",
        "eval:knowledge-qa:tabular",
        "eval:knowledge-qa:visual",
        "eval:safety:harmful",
        "eval:safety:copyright",
        "eval:safety:xpia",
    ]
    for tag in valid:
        p = yaml_file(tmp_path, f"tags: [{tag}]\n")
        assert validate_file(p) == [], f"Expected {tag!r} to be valid"


# ---------------------------------------------------------------------------
# Combined domain: + eval: tags
# ---------------------------------------------------------------------------


def test_valid_domain_and_eval_together_pass(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:banking, eval:orchestration:tool-selection]\n")
    assert validate_file(p) == []


def test_invalid_domain_and_invalid_eval_both_reported(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:foo, eval:bar]\n")
    errors = validate_file(p)
    assert any("foo" in e for e in errors)
    assert any("bar" in e for e in errors)


def test_valid_domain_invalid_eval_only_eval_reported(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:sales, eval:bar]\n")
    errors = validate_file(p)
    assert all("eval" in e for e in errors)
    assert len(errors) == 1


def test_invalid_domain_valid_eval_only_domain_reported(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:foo, eval:knowledge-qa:tabular]\n")
    errors = validate_file(p)
    assert all("domain" in e for e in errors)
    assert len(errors) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_tags_line_with_other_non_domain_tags_passes(tmp_path):
    """Labels and skip tags should not trigger validation errors."""
    p = yaml_file(tmp_path, "tags: [domain:misc, eval:safety:xpia, baseline, skip]\n")
    assert validate_file(p) == []


def test_tags_with_trailing_comma_in_value_handled(tmp_path):
    """Trailing comma after tag value inside the list should be stripped."""
    p = yaml_file(tmp_path, "tags: [domain:foo, eval:orchestration:tool-selection]\n")
    errors = validate_file(p)
    assert any("foo" in e for e in errors)
    assert not any("orchestration" in e for e in errors)


# ---------------------------------------------------------------------------
# Mutual exclusivity — at most one domain: and one eval: per scenario
# ---------------------------------------------------------------------------


def test_duplicate_domain_tags_fail(tmp_path):
    p = yaml_file(tmp_path, "tags: [domain:sales, domain:hr]\n")
    errors = validate_file(p)
    assert any("multiple domain" in e for e in errors)
    assert any("sales" in e for e in errors)
    assert any("hr" in e for e in errors)


def test_duplicate_eval_tags_fail(tmp_path):
    p = yaml_file(tmp_path, "tags: [eval:knowledge-qa:text, eval:orchestration:tool-selection]\n")
    errors = validate_file(p)
    assert any("multiple eval" in e for e in errors)
    assert any("knowledge-qa:text" in e for e in errors)
    assert any("orchestration:tool-selection" in e for e in errors)


def test_single_domain_with_other_tags_passes(tmp_path):
    """Non-domain/eval tags should not affect the domain count."""
    p = yaml_file(tmp_path, "tags: [domain:banking, eval:orchestration:tool-selection, baseline]\n")
    assert validate_file(p) == []


def test_duplicate_domain_and_invalid_value_both_reported(tmp_path):
    """Both the duplicate error and the invalid-value error should surface."""
    p = yaml_file(tmp_path, "tags: [domain:sales, domain:foo]\n")
    errors = validate_file(p)
    assert any("unrecognised domain" in e and "foo" in e for e in errors)
    assert any("multiple domain" in e for e in errors)
