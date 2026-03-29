"""Tests for repo-context resolution consistency.

Verifies that snapshot, watch, and export all use the same
repo-context resolution path.
"""
from unittest.mock import patch
from doghouse.cli.main import resolve_repo_context


def test_resolve_explicit_repo_and_pr():
    """When both --repo and --pr are provided, no auto-detection needed."""
    repo, owner, name, pr = resolve_repo_context("flyingrobots/draft-punks", 42)
    assert repo == "flyingrobots/draft-punks"
    assert owner == "flyingrobots"
    assert name == "draft-punks"
    assert pr == 42


def test_resolve_parses_owner_name_from_repo_string():
    """The repo string should be split into owner and name."""
    _repo, owner, name, _pr = resolve_repo_context("acme/widgets", 7)
    assert owner == "acme"
    assert name == "widgets"


def test_resolve_handles_repo_without_slash():
    """When repo has no slash, both owner and name become the same string."""
    repo, owner, name, pr = resolve_repo_context("widgets", 7)
    assert repo == "widgets"
    assert owner == "widgets"
    assert name == "widgets"
    assert pr == 7


@patch("doghouse.cli.main._auto_detect_repo_and_pr")
def test_resolve_auto_detects_when_repo_missing(mock_detect):
    """When --repo is not provided, auto-detection fills it in."""
    mock_detect.return_value = ("detected/repo", 99)
    repo, owner, name, pr = resolve_repo_context(None, None)
    assert repo == "detected/repo"
    assert owner == "detected"
    assert name == "repo"
    assert pr == 99
    mock_detect.assert_called_once()


@patch("doghouse.cli.main._auto_detect_repo_and_pr")
def test_resolve_auto_detects_pr_only(mock_detect):
    """When --repo is provided but --pr is not, detect only PR."""
    mock_detect.return_value = ("ignored/repo", 55)
    repo, owner, name, pr = resolve_repo_context("my/repo", None)
    assert repo == "my/repo"
    assert owner == "my"
    assert name == "repo"
    assert pr == 55


def test_all_commands_share_resolve_repo_context():
    """Structural assertion: snapshot, watch, and export must call resolve_repo_context.

    This is a source-inspection guard, not a behavioral test.  It catches
    regressions where a new command bypasses the centralized helper.  It will
    break if the function is renamed — that's intentional (update both).
    """
    import inspect
    from doghouse.cli import main

    for cmd_name in ["snapshot", "watch", "export"]:
        fn = getattr(main, cmd_name)
        source = inspect.getsource(fn)
        assert "resolve_repo_context" in source, (
            f"{cmd_name} does not use resolve_repo_context — "
            f"repo context will be inconsistent"
        )
