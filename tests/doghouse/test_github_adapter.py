"""Tests for GitHub adapter blocker collection semantics."""

from doghouse.adapters.github.gh_cli_adapter import GhCliAdapter
from doghouse.core.domain.blocker import BlockerType, BlockerSeverity


def _make_adapter(review_threads: list[dict], review_decision: str = "APPROVED") -> GhCliAdapter:
    adapter = GhCliAdapter(repo_owner="flyingrobots", repo_name="draft-punks")

    def fake_run(args: list[str], with_repo: bool = True) -> dict:
        if args[:2] == ["pr", "view"]:
            return {
                "statusCheckRollup": [],
                "reviewDecision": review_decision,
                "mergeable": "MERGEABLE",
                "number": 5,
            }
        if args[:2] == ["api", "graphql"]:
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "nodes": review_threads,
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                            }
                        }
                    }
                }
            }
        raise AssertionError(f"Unexpected gh args: {args}")

    adapter._run_gh_json = fake_run  # type: ignore[method-assign]
    adapter._fetch_repo_info = lambda: ("flyingrobots", "draft-punks")  # type: ignore[method-assign]
    return adapter


def test_fetch_blockers_ignores_outdated_threads():
    adapter = _make_adapter([
        {
            "isResolved": False,
            "isOutdated": False,
            "comments": {"nodes": [{"body": "Live thread", "id": "live"}]},
        },
        {
            "isResolved": False,
            "isOutdated": True,
            "comments": {"nodes": [{"body": "Outdated thread", "id": "outdated"}]},
        },
        {
            "isResolved": True,
            "isOutdated": False,
            "comments": {"nodes": [{"body": "Resolved thread", "id": "resolved"}]},
        },
    ])

    blockers = adapter.fetch_blockers(5)

    assert [(b.id, b.type) for b in blockers] == [
        ("thread-live", BlockerType.UNRESOLVED_THREAD),
    ]


def test_changes_requested_with_only_outdated_threads_yields_reapproval_warning():
    adapter = _make_adapter(
        [
            {
                "isResolved": False,
                "isOutdated": True,
                "comments": {"nodes": [{"body": "Outdated thread", "id": "outdated"}]},
            }
        ],
        review_decision="CHANGES_REQUESTED",
    )

    blockers = adapter.fetch_blockers(5)

    assert [(b.id, b.type, b.severity) for b in blockers] == [
        (
            "review-changes-requested",
            BlockerType.NOT_APPROVED,
            BlockerSeverity.WARNING,
        ),
    ]
