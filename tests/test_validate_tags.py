# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for the check_tag_values helper in scripts/validate_tags.py."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_tags import check_tag_values, _VALID_DOMAINS, _VALID_EVALS
from thinkingbox.common.tag_types import Domain, Eval, TestCaseTags


def make_tags(**kwargs) -> TestCaseTags:
    """Construct a TestCaseTags via model_construct, bypassing Pydantic validation.

    This lets us inject invalid values (e.g. domain="foo") to test the error path,
    which would otherwise be rejected by the Pydantic model.
    """
    defaults = {"labels": [], "category": [], "domain": None, "eval_type": None, "skip": False}
    defaults.update(kwargs)
    return TestCaseTags.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Valid tags — no errors expected
# ---------------------------------------------------------------------------


def test_no_tags_produces_no_errors():
    tags = make_tags()
    assert check_tag_values(tags) == []


def test_all_valid_domain_values_pass():
    for domain in Domain:
        tags = make_tags(domain=domain)
        assert check_tag_values(tags) == [], f"Expected {domain!r} to be valid"


def test_all_valid_eval_values_pass():
    for eval_type in Eval:
        tags = make_tags(eval_type=eval_type)
        assert check_tag_values(tags) == [], f"Expected {eval_type!r} to be valid"


def test_valid_domain_and_eval_together_pass():
    tags = make_tags(domain=Domain.BANKING, eval_type=Eval.ORCHESTRATION_TOOL_SELECTION)
    assert check_tag_values(tags) == []


# ---------------------------------------------------------------------------
# Invalid domain
# ---------------------------------------------------------------------------


def test_invalid_domain_string_caught():
    tags = make_tags(domain="foo")
    errors = check_tag_values(tags)
    assert len(errors) == 1
    assert "domain" in errors[0]
    assert "foo" in errors[0]


def test_invalid_domain_error_lists_valid_values():
    tags = make_tags(domain="not-a-domain")
    errors = check_tag_values(tags)
    assert any(v in errors[0] for v in _VALID_DOMAINS)


# ---------------------------------------------------------------------------
# Invalid eval
# ---------------------------------------------------------------------------


def test_invalid_eval_string_caught():
    tags = make_tags(eval_type="bar")
    errors = check_tag_values(tags)
    assert len(errors) == 1
    assert "eval" in errors[0]
    assert "bar" in errors[0]


def test_invalid_eval_error_lists_valid_values():
    tags = make_tags(eval_type="not-an-eval")
    errors = check_tag_values(tags)
    assert any(v in errors[0] for v in _VALID_EVALS)


# ---------------------------------------------------------------------------
# Both invalid
# ---------------------------------------------------------------------------


def test_both_invalid_domain_and_eval_reported():
    tags = make_tags(domain="foo", eval_type="bar")
    errors = check_tag_values(tags)
    assert any("foo" in e for e in errors)
    assert any("bar" in e for e in errors)
    assert len(errors) == 2


def test_invalid_domain_valid_eval_only_domain_reported():
    tags = make_tags(domain="foo", eval_type=Eval.KNOWLEDGE_QA_TEXT)
    errors = check_tag_values(tags)
    assert len(errors) == 1
    assert "domain" in errors[0]


def test_valid_domain_invalid_eval_only_eval_reported():
    tags = make_tags(domain=Domain.SALES, eval_type="bar")
    errors = check_tag_values(tags)
    assert len(errors) == 1
    assert "eval" in errors[0]


# ---------------------------------------------------------------------------
# None values are always valid (tags are optional)
# ---------------------------------------------------------------------------


def test_none_domain_is_valid():
    tags = make_tags(domain=None, eval_type=Eval.SAFETY_XPIA)
    assert check_tag_values(tags) == []


def test_none_eval_is_valid():
    tags = make_tags(domain=Domain.HUMAN_RESOURCES, eval_type=None)
    assert check_tag_values(tags) == []
