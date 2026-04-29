# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Full-stack tag validation across a dataset's Python test-case files.

USE CASE
--------
Developer-facing diagnostic tool for validating and reporting on tags across
an entire dataset. Unlike validate_scenario_tags.py, this script exercises the
full ThinkingBox hydration pipeline — loading scenario YAMLs, resolving
inheritance, merging scenario- and test-case-level tags — and reports on the
resulting hydrated tags.

Use this when you want to:
  - Verify that all test cases load and hydrate without errors
  - Get a coverage report of domain: and eval: tag usage across the dataset
  - Identify tests that are missing domain: or eval: tags
  - Inspect the final (post-inheritance) tag values per test case

This script is intentionally slow (it loads the hydrator and all test files)
and is not suitable as a pre-commit hook. For fast, file-scoped validation of
scenario YAML tag values, see validate_scenario_tags.py instead.

Usage:
    python validate_tags.py                          # validate full dataset
    python validate_tags.py --file test_case/foo.py  # single file
    python validate_tags.py --dataset ./dataset --agent think --verbose

Exits non-zero if any test case fails to hydrate or contains unrecognised tag
values. Missing tags produce warnings, not errors.
"""


import sys
import traceback
from pathlib import Path
from collections import defaultdict
from thinkingbox.common.hydrator import Dataset, iter_cases_from_file_or_folder
from thinkingbox.common.tag_types import Domain, Eval, TestCaseTags

_VALID_DOMAINS = {d.value for d in Domain}
_VALID_EVALS = {e.value for e in Eval}


def check_tag_values(tags: TestCaseTags) -> list[str]:
    """Return error strings for any tag values that are not recognised enum members.

    Under normal hydration Pydantic enforces valid enum values, so this primarily
    catches cases where TestCaseTags was constructed via model_construct() or
    similar bypass, and provides a targeted error message instead of a raw
    Pydantic ValidationError traceback.
    """
    errors: list[str] = []
    if tags.domain is not None and not isinstance(tags.domain, Domain):
        errors.append(
            f"unrecognised domain value {tags.domain!r} (valid: {sorted(_VALID_DOMAINS)})"
        )
    if tags.eval_type is not None and not isinstance(tags.eval_type, Eval):
        errors.append(
            f"unrecognised eval value {tags.eval_type!r} (valid: {sorted(_VALID_EVALS)})"
        )
    return errors

def capture_error_details(exception: Exception, context: str = "", test_identifier: str = "") -> dict:
    """Capture detailed error information including stack trace."""
    tb = traceback.extract_tb(exception.__traceback__)
    
    # Get the most relevant frame (usually the last one in our code)
    relevant_frame = None
    for frame in reversed(tb):
        if 'validate_tags.py' in frame.filename or 'hydrator' in frame.filename:
            relevant_frame = frame
            break
    
    if not relevant_frame:
        relevant_frame = tb[-1] if tb else None
    
    error_details = {
        "error_type": exception.__class__.__name__,
        "error_message": str(exception),
        "context": context,
        "test_identifier": test_identifier,
        "stack_trace": traceback.format_exc(),
        "file": relevant_frame.filename if relevant_frame else "unknown",
        "line": relevant_frame.lineno if relevant_frame else "unknown",
        "code": relevant_frame.line if relevant_frame else "unknown"
    }
    
    return error_details

def print_table(headers: list[str], rows: list[list], widths: list[int] = None):
    """Print a formatted table."""
    if not rows:
        return
    
    # Auto-calculate widths if not provided
    if widths is None:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_line = "│ " + " │ ".join(h.ljust(w) for h, w in zip(headers, widths)) + " │"
    separator = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
    top_line = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
    bottom_line = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"
    
    print(top_line)
    print(header_line)
    print(separator)
    
    # Print rows
    for row in rows:
        row_line = "│ " + " │ ".join(str(cell).ljust(w) for cell, w in zip(row, widths)) + " │"
        print(row_line)
    
    print(bottom_line)

def validate_tags(dataset_path: str = "./dataset", agent_name: str = "think", 
                  test_file: str = None, verbose: bool = False):
    """Validate that tags are working correctly in scenarios and test cases."""
    
    # Convert to absolute path for consistent path operations
    dataset_path = Path(dataset_path).resolve()
    dataset = Dataset(dataset_path)
    test_case_dir = dataset_path / "test_case"
    
    if not test_case_dir.exists():
        print(f"❌ Test case directory not found: {test_case_dir}")
        return False
    
    # Find test files to check
    if test_file:
        specific_file = Path(test_file)
        if not specific_file.is_absolute():
            # If path already starts with test_case/, use it relative to dataset_path
            if test_file.startswith("test_case/"):
                specific_file = Path(dataset_path) / test_file
            else:
                specific_file = test_case_dir / test_file
        
        if not specific_file.exists():
            print(f"❌ Test file not found: {specific_file}")
            return False
        
        validate_path = specific_file
        test_files_count = 1
        print(f"📄 Checking specific file: {test_file}\n")
    else:
        validate_path = test_case_dir
        test_files = list(test_case_dir.glob("**/*.py"))
        test_files_count = len(test_files)
        
        if not test_files:
            print(f"❌ No test files found in {test_case_dir}")
            return False
        
        print(f"📁 Found {test_files_count} test files\n")
    
    # Load agent once
    try:
        agent = dataset.get_agent_config(agent_name)
    except Exception as e:
        error_details = capture_error_details(e, context=f"Loading agent '{agent_name}'")
        
        print(f"❌ Could not load agent '{agent_name}': {e}")
        if verbose:
            print(f"Stack trace:\n{error_details['stack_trace']}")
        return False
    
    # Statistics with detailed error tracking
    stats = {
        'total_files': test_files_count,
        'total_tests': 0,
        'skipped_tests': 0,
        'tests_with_domain': 0,
        'tests_without_domain': 0,
        'tests_with_eval': 0,
        'tests_without_eval': 0,
        'failed_files': [],
        'failed_tests': [],
        'detailed_errors': [],
        'skipped_test_list': [],
        'tests_without_domain_list': [],
        'tests_without_eval_list': [],
        'test_case_domains': defaultdict(int),
        'scenario_domains': defaultdict(int),
        'final_domains': defaultdict(int),
        'final_evals': defaultdict(int),
        'categories': defaultdict(int),
        'scenarios_checked': set(),
        'current_file': None,
    }
    
    try:
        for hydrated in iter_cases_from_file_or_folder(
            path=validate_path,
            base_dir=dataset_path,
            agent=agent_name,
            skip_filtered=False,
        ):
            # Initialize these early so they're available in exception handler
            test_name = None
            test_file_path = None
            test_identifier = "unknown"
            
            try:
                stats['total_tests'] += 1
                
                # Track file changes for verbose output
                test_file_path = Path(hydrated.metadata['test_case_file'])
                if test_file_path != stats['current_file']:
                    stats['current_file'] = test_file_path
                    
                    if verbose or test_file:
                        print(f"\n{'='*80}")
                        print(f"📄 File: {test_file_path.relative_to(dataset_path)}")
                        print(f"{'='*80}")
                
                # Get test identifier
                test_name = hydrated.metadata['test_case_name']
                test_identifier = f"{test_file_path.relative_to(dataset_path)}:{test_name}"
                
                if verbose or test_file:
                    print(f"\n  📝 Test: {test_name}")
                    print(f"     Scenario: {hydrated.metadata['scenario']}")
                
                # Track scenario
                stats['scenarios_checked'].add(hydrated.metadata['scenario'])
                
                # Check if skipped (after hydration)
                if hydrated.tags.skip:
                    stats['skipped_tests'] += 1
                    stats['skipped_test_list'].append(test_identifier)
                    if verbose or test_file:
                        print(f"     ⏭️  SKIPPED")
                    continue

                # Validate tag enum values
                tag_errors = check_tag_values(hydrated.tags)
                if tag_errors:
                    for err in tag_errors:
                        error_msg = f"{test_identifier}: {err}"
                        stats['failed_tests'].append(error_msg)
                        if verbose or test_file:
                            print(f"     ❌ Tag error: {err}")

                # Count scenario domains
                if hydrated.scenario.tags and hydrated.scenario.tags.domain:
                    stats['scenario_domains'][hydrated.scenario.tags.domain] += 1
                
                # Count final domains, evals, and categories (after hydration)
                if hydrated.tags.domain:
                    stats['final_domains'][hydrated.tags.domain] += 1
                    stats['tests_with_domain'] += 1
                else:
                    stats['tests_without_domain'] += 1
                    stats['tests_without_domain_list'].append(test_identifier)

                if hydrated.tags.eval_type:
                    stats['final_evals'][hydrated.tags.eval_type] += 1
                    stats['tests_with_eval'] += 1
                else:
                    stats['tests_without_eval'] += 1
                    stats['tests_without_eval_list'].append(test_identifier)

                for cat in hydrated.tags.category:
                    stats['categories'][cat] += 1

                if verbose or test_file:
                    print(f"     Scenario tags:")
                    if hydrated.scenario.tags:
                        print(f"       - Domain: {hydrated.scenario.tags.domain}")
                        print(f"       - Eval: {hydrated.scenario.tags.eval_type}")
                        print(f"       - Categories: {hydrated.scenario.tags.category}")
                        print(f"       - Labels: {hydrated.scenario.tags.labels}")
                    else:
                        print(f"       None")

                    print(f"     Final tags (after hydration):")
                    print(f"       - Domain: {hydrated.tags.domain}")
                    print(f"       - Eval: {hydrated.tags.eval_type}")
                    print(f"       - Categories: {hydrated.tags.category}")
                    print(f"       - Labels: {hydrated.tags.labels}")
                    print(f"       - Skip: {hydrated.tags.skip}")
                    
            except Exception as e:
                # Build context safely
                context = "Processing test case"
                if test_name:
                    context += f" '{test_name}'"
                if test_file_path:
                    try:
                        context += f" in file '{test_file_path.relative_to(dataset_path)}'"
                    except:
                        context += f" in file '{test_file_path}'"
                
                error_details = capture_error_details(
                    e, 
                    context=context,
                    test_identifier=test_identifier
                )
                stats['detailed_errors'].append(error_details)
                
                error_msg = f"{test_identifier}: {e}"
                stats['failed_tests'].append(error_msg)
                
                if verbose or test_file:
                    print(f"     ❌ Processing failed: {e}")
                    if verbose:
                        print(f"     📍 Error location: {error_details['file']}:{error_details['line']}")
                        print(f"     💾 Code: {error_details['code']}")
                    
    except Exception as e:
        error_details = capture_error_details(
            e, 
            context=f"Loading test files from '{validate_path}'",
            test_identifier=str(validate_path)
        )
        stats['detailed_errors'].append(error_details)
        
        error_msg = f"{validate_path}: {e}"
        stats['failed_files'].append(error_msg)
        
        if verbose:
            print(f"❌ Failed to load files: {e}")
            if verbose:
                print(f"📍 Error location: {error_details['file']}:{error_details['line']}")
                print(f"💾 Code: {error_details['code']}")
    
    # Calculate success
    has_errors = len(stats['failed_files']) > 0 or len(stats['failed_tests']) > 0
    has_warnings = stats['tests_without_domain'] > 0
    stats['success'] = not has_errors
    stats['error_count'] = len(stats['failed_files']) + len(stats['failed_tests'])
    stats['warning_count'] = stats['tests_without_domain']
    
    # Convert sets to lists for JSON serialization
    stats['scenarios_checked'] = list(stats['scenarios_checked'])
    
    # Print concise summary
    print(f"\n{'='*80}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    # Summary table
    summary_rows = [
        ["Total Test Files", stats['total_files']],
        ["Total Test Cases", stats['total_tests']],
        ["Successfully Loaded", stats['total_files'] - len(stats['failed_files'])],
        ["Failed Files", len(stats['failed_files'])],
        ["Failed Tests", len(stats['failed_tests'])],
        ["Skipped Tests", stats['skipped_tests']],
        ["Unique Scenarios", len(stats['scenarios_checked'])],
    ]
    print_table(["Metric", "Count"], summary_rows, [40, 10])
    
    # Domain coverage table
    print(f"\n🏷️  DOMAIN COVERAGE")
    print("─" * 80)
    domain_rows = [
        ["With Domain", stats['tests_with_domain']],
        ["Without Domain", stats['tests_without_domain']],
    ]
    print_table(["Status", "Count"], domain_rows, [50, 10])

    if stats['final_domains']:
        print(f"\n📊 DOMAIN DISTRIBUTION (after hydration)")
        print("─" * 80)
        total = sum(stats['final_domains'].values())
        domain_dist_rows = []
        for domain, count in sorted(stats['final_domains'].items(), key=lambda x: -x[1]):
            percentage = (count / total) * 100
            domain_dist_rows.append([domain, count, f"{percentage:.1f}%"])
        print_table(["Domain", "Count", "%"], domain_dist_rows, [50, 10, 10])

    # Eval coverage table
    print(f"\n⚙️  EVAL COVERAGE")
    print("─" * 80)
    task_rows = [
        ["With Eval", stats['tests_with_eval']],
        ["Without Eval", stats['tests_without_eval']],
    ]
    print_table(["Status", "Count"], task_rows, [50, 10])

    if stats['final_evals']:
        print(f"\n📊 EVAL DISTRIBUTION (after hydration)")
        print("─" * 80)
        total = sum(stats['final_evals'].values())
        task_dist_rows = []
        for eval_type, count in sorted(stats['final_evals'].items(), key=lambda x: -x[1]):
            percentage = (count / total) * 100
            task_dist_rows.append([eval_type, count, f"{percentage:.1f}%"])
        print_table(["Eval", "Count", "%"], task_dist_rows, [50, 10, 10])
    
    if stats['categories']:
        print(f"\n📂 CATEGORY DISTRIBUTION (after hydration)")
        print("─" * 80)
        cat_rows = []
        for category, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            cat_rows.append([category, count])
        print_table(["Category", "Count"], cat_rows, [50, 10])
    
    # Highlight issues
    print(f"\n{'='*80}")
    print(f"⚠️  ISSUES & WARNINGS")
    print(f"{'='*80}\n")
    
    issues_found = False
    
    if stats['failed_files']:
        issues_found = True
        print(f"❌ FAILED FILES ({len(stats['failed_files'])})")
        print("─" * 80)
        for error in stats['failed_files']:
            print(f"   • {error}")
        print()
    
    if stats['failed_tests']:
        issues_found = True
        print(f"❌ FAILED TESTS ({len(stats['failed_tests'])})")
        print("─" * 80)
        for error in stats['failed_tests']:
            print(f"   • {error}")
            print()
        print()
    
    if stats['tests_without_domain_list']:
        issues_found = True
        print(f"⚠️  TESTS WITHOUT DOMAIN ({len(stats['tests_without_domain_list'])})")
        print("─" * 80)
        print("These tests are missing domain tags. Please add domain tags to scenarios or test cases:")
        for test in stats['tests_without_domain_list']:
            print(f"   • {test}")
        print()

    if stats['tests_without_eval_list']:
        issues_found = True
        print(f"⚠️  TESTS WITHOUT EVAL ({len(stats['tests_without_eval_list'])})")
        print("─" * 80)
        print("These tests are missing eval: tags. Please add eval: tags to scenarios or test cases:")
        for test in stats['tests_without_eval_list']:
            print(f"   • {test}")
        print()
    
    if stats['skipped_test_list'] and verbose:
        print(f"⏭️  SKIPPED TESTS ({len(stats['skipped_test_list'])})")
        print("─" * 80)
        for test in stats['skipped_test_list']:
            print(f"   • {test}")
        print()
    
    if not issues_found:
        print("✅ No issues found!\n")
    
    # Detailed errors if verbose
    if verbose and stats['detailed_errors']:
        print(f"\n{'='*80}")
        print(f"🔍 DETAILED ERROR INFORMATION")
        print(f"{'='*80}\n")
        for i, error in enumerate(stats['detailed_errors'], 1):
            print(f"{i}. {error['error_type']}: {error['error_message']}")
            print(f"   Context: {error['context']}")
            if error['test_identifier']:
                print(f"   Test: {error['test_identifier']}")
            print(f"   Location: {error['file']}:{error['line']}")
            print(f"   Code: {error['code']}")
            if verbose:
                print(f"   Stack trace:")
                for line in error['stack_trace'].split('\n'):
                    if line.strip():
                        print(f"     {line}")
            print()
    
    # Final verdict
    print(f"{'='*80}")
    if has_errors:
        print(f"❌ VALIDATION FAILED")
        print(f"   Errors: {stats['error_count']}")
        if has_warnings:
            print(f"   Warnings: {stats['warning_count']} (tests without domain)")
    elif has_warnings:
        print(f"⚠️  VALIDATION PASSED WITH WARNINGS")
        print(f"   Warnings: {stats['warning_count']} (tests without domain)")
    else:
        print(f"✅ VALIDATION PASSED")
        print(f"   All {stats['total_tests']} test cases validated successfully!")
    print(f"{'='*80}\n")
    
    return not has_errors

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate tags in test cases")
    parser.add_argument(
        "--dataset",
        default="./dataset",
        help="Path to dataset directory (default: ./dataset)"
    )
    parser.add_argument(
        "--agent",
        default="think",
        help="Agent name to use for hydration (default: think)"
    )
    parser.add_argument(
        "--file",
        help="Specific test file to validate (relative to dataset/test_case/ or absolute path)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output for each test case and full stack traces"
    )
    
    args = parser.parse_args()
    
    try:
        result = validate_tags(
            args.dataset, 
            args.agent, 
            test_file=args.file, 
            verbose=args.verbose,
        )
        
        sys.exit(0 if result else 1)
            
    except KeyboardInterrupt:
        raise
    except Exception as e:
        error_details = capture_error_details(e, context="Main execution")
        
        print(f"\n❌ Fatal error during validation: {e}")
        if args.verbose:
            print(f"\nFull stack trace:")
            print(error_details['stack_trace'])
    
        sys.exit(3)