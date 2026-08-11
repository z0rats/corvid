"""_record_mention/_person_to_dict/_analyst_to_result reconstruct per-repo
mention provenance that gitcolombo.Person itself doesn't retain (it only
keeps a single last-seen repo/commit per identity - see the module docstring
comment above _run_clone_mode_sync in git_recon_service.py). These tests
exercise that aggregation directly against real gitcolombo.Person/GitAnalyst
objects, without going through an actual git clone."""
from collections import defaultdict

import gitcolombo

from app.features.git_recon.service.git_recon_service import (
    _analyst_to_result,
    _person_to_dict,
    _record_mention,
    _track_commits_per_repo,
    build_mentions,
)

# --- _record_mention --------------------------------------------------------


def test_record_mention_counts_author_and_committer_separately():
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)

    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha1", role="as_author")
    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha2", role="as_committer")

    entry = mentions["alice"]["https://github.com/o/repo"]
    assert entry["as_author"] == 1
    assert entry["as_committer"] == 1


def test_record_mention_accumulates_across_multiple_commits_same_repo():
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)

    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha1", role="as_author")
    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha2", role="as_author")
    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha3", role="as_author")

    assert mentions["alice"]["https://github.com/o/repo"]["as_author"] == 3


def test_record_mention_sample_commit_is_the_first_seen_for_that_repo():
    # setdefault() only writes sample_commit on the first mention of a given
    # person+repo pair; later commits in the same repo increment the counter
    # but must not overwrite the recorded sample_commit.
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)

    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha_first", role="as_author")
    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha_second", role="as_author")

    assert mentions["alice"]["https://github.com/o/repo"]["sample_commit"] == "sha_first"


def test_record_mention_tracks_separate_repos_independently():
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)

    _record_mention(mentions, "alice", "https://github.com/o/repo1", "sha1", role="as_author")
    _record_mention(mentions, "alice", "https://github.com/o/repo2", "sha2", role="as_author")

    assert set(mentions["alice"].keys()) == {"https://github.com/o/repo1", "https://github.com/o/repo2"}
    assert mentions["alice"]["https://github.com/o/repo1"]["as_author"] == 1
    assert mentions["alice"]["https://github.com/o/repo2"]["as_author"] == 1


def test_record_mention_tracks_separate_persons_independently():
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)

    _record_mention(mentions, "alice", "https://github.com/o/repo", "sha1", role="as_author")
    _record_mention(mentions, "bob", "https://github.com/o/repo", "sha1", role="as_committer")

    assert mentions["alice"]["https://github.com/o/repo"]["as_author"] == 1
    assert mentions["alice"]["https://github.com/o/repo"]["as_committer"] == 0
    assert mentions["bob"]["https://github.com/o/repo"]["as_committer"] == 1
    assert mentions["bob"]["https://github.com/o/repo"]["as_author"] == 0


# --- build_mentions ------------------------------------------------------


def _make_commit(hash, author, committer, author_name="", author_email="", committer_name="", committer_email=""):
    return gitcolombo.Commit(
        hash=hash, author=author, committer=committer,
        author_name=author_name, author_email=author_email,
        committer_name=committer_name, committer_email=committer_email,
    )


def test_build_mentions_attributes_commits_to_their_own_repo():
    commits_by_repo = {
        "https://github.com/o/repo1": [_make_commit("sha1", "alice", "alice")],
        "https://github.com/o/repo2": [_make_commit("sha2", "alice", "alice")],
    }

    mentions = build_mentions(commits_by_repo)

    assert set(mentions["alice"].keys()) == {
        "https://github.com/o/repo1",
        "https://github.com/o/repo2",
    }
    assert mentions["alice"]["https://github.com/o/repo1"]["repo_url"] == "https://github.com/o/repo1"
    assert mentions["alice"]["https://github.com/o/repo2"]["repo_url"] == "https://github.com/o/repo2"


def test_build_mentions_counts_author_and_committer_across_multiple_commits():
    commits_by_repo = {
        "https://github.com/o/repo": [
            _make_commit("sha1", "alice", "bob"),
            _make_commit("sha2", "alice", "alice"),
        ],
    }

    mentions = build_mentions(commits_by_repo)

    entry = mentions["alice"]["https://github.com/o/repo"]
    assert entry["as_author"] == 2
    assert entry["as_committer"] == 1
    assert mentions["bob"]["https://github.com/o/repo"]["as_committer"] == 1


def test_build_mentions_handles_empty_commits_by_repo():
    assert build_mentions({}) == {}


# --- _track_commits_per_repo --------------------------------------------


class _FakeAnalyst:
    """Stands in for gitcolombo.GitAnalyst: .append(url, cloned_path) appends
    however many fake commits `commits_per_url` says that url is worth to
    .commits, mirroring how the real GitAnalyst.append() grows analyst.commits
    in place as it walks a repo's `git log --all`."""

    def __init__(self, commits_per_url: dict[str, int]):
        self._commits_per_url = commits_per_url
        self.commits: list[object] = []
        self.appended_urls: list[str] = []

    def append(self, url, cloned_path=None):
        self.appended_urls.append(url)
        for _ in range(self._commits_per_url.get(url, 0)):
            self.commits.append(object())


def test_track_commits_per_repo_gives_each_repo_its_own_slice_only():
    analyst = _FakeAnalyst({"repo1": 2, "repo2": 3})
    cloned = {"repo1": "/tmp/repo1", "repo2": "/tmp/repo2"}

    commits_by_repo = _track_commits_per_repo(analyst, cloned)

    assert len(commits_by_repo["repo1"]) == 2
    assert len(commits_by_repo["repo2"]) == 3
    assert set(commits_by_repo["repo1"]) & set(commits_by_repo["repo2"]) == set()
    assert commits_by_repo["repo1"] == analyst.commits[0:2]
    assert commits_by_repo["repo2"] == analyst.commits[2:5]


def test_track_commits_per_repo_skips_repos_with_failed_clone():
    analyst = _FakeAnalyst({"repo1": 2})
    cloned = {"repo1": "/tmp/repo1", "repo2": None}

    commits_by_repo = _track_commits_per_repo(analyst, cloned)

    assert "repo2" not in commits_by_repo
    assert analyst.appended_urls == ["repo1"]


def test_track_commits_per_repo_zero_commit_repo_does_not_shift_the_next_slice():
    analyst = _FakeAnalyst({"repo1": 0, "repo2": 3})
    cloned = {"repo1": "/tmp/repo1", "repo2": "/tmp/repo2"}

    commits_by_repo = _track_commits_per_repo(analyst, cloned)

    assert commits_by_repo["repo1"] == []
    assert len(commits_by_repo["repo2"]) == 3
    assert commits_by_repo["repo2"] == analyst.commits


def test_track_commits_per_repo_orders_result_by_cloned_processing_order():
    analyst = _FakeAnalyst({"repo_b": 1, "repo_a": 1, "repo_c": 1})
    cloned = {"repo_b": "/tmp/b", "repo_a": "/tmp/a", "repo_c": "/tmp/c"}

    commits_by_repo = _track_commits_per_repo(analyst, cloned)

    assert list(commits_by_repo.keys()) == ["repo_b", "repo_a", "repo_c"]


# --- _person_to_dict ---------------------------------------------------


def _make_person(key, name, email, as_author=0, as_committer=0, github_login=None, also_known=None):
    return gitcolombo.Person(
        key=key, name=name, email=email,
        as_author=as_author, as_committer=as_committer,
        github_login=github_login, also_known=also_known or {},
    )


def test_person_to_dict_includes_core_fields_and_noreply_flag():
    person = _make_person("alice", "Alice", "alice@users.noreply.github.com", as_author=5, as_committer=2)

    result = _person_to_dict(person)

    assert result["key"] == "alice"
    assert result["name"] == "Alice"
    assert result["is_noreply"] is True


def test_person_to_dict_flags_real_email_as_not_noreply():
    person = _make_person("bob", "Bob", "bob@example.com")

    result = _person_to_dict(person)

    assert result["is_noreply"] is False


def test_person_to_dict_includes_aliases_with_their_own_noreply_flag():
    alias = _make_person("bob-work", "Bob W.", "bob@company.com")
    person = _make_person("bob", "Bob", "bob@users.noreply.github.com", also_known={"bob-work": alias})

    result = _person_to_dict(person)

    assert len(result["aliases"]) == 1
    assert result["aliases"][0]["email"] == "bob@company.com"
    assert result["aliases"][0]["is_noreply"] is False


def test_person_to_dict_sorts_mentions_by_total_activity_descending():
    mentions = {
        "https://github.com/o/quiet-repo": {
            "repo_url": "https://github.com/o/quiet-repo", "sample_commit": "s1", "as_author": 1, "as_committer": 0,
        },
        "https://github.com/o/busy-repo": {
            "repo_url": "https://github.com/o/busy-repo", "sample_commit": "s2", "as_author": 10, "as_committer": 5,
        },
    }
    person = _make_person("alice", "Alice", "alice@example.com")

    result = _person_to_dict(person, mentions)

    assert [m["repo_url"] for m in result["mentions"]] == [
        "https://github.com/o/busy-repo",
        "https://github.com/o/quiet-repo",
    ]


def test_person_to_dict_handles_no_mentions():
    person = _make_person("alice", "Alice", "alice@example.com")

    result = _person_to_dict(person, None)

    assert result["mentions"] == []


# --- _analyst_to_result -------------------------------------------------


def _make_analyst(persons=(), name_to_emails=None, same_emails_persons=None, commits_count=0, repos=()):
    analyst = gitcolombo.GitAnalyst()
    analyst.persons = {p.key: p for p in persons}
    analyst.name_to_emails = name_to_emails or {}
    analyst.same_emails_persons = same_emails_persons or {}
    analyst.commits = [object()] * commits_count
    analyst.repos = list(repos)
    return analyst


def test_analyst_to_result_reports_correct_stats():
    alice = _make_person("alice", "Alice", "alice@example.com")
    bob = _make_person("bob", "Bob", "bob@example.com")
    analyst = _make_analyst(persons=[alice, bob], commits_count=7, repos=["repo1"])

    result = _analyst_to_result(analyst, repo_outcomes=[{"url": "repo1", "cloned": True}], notes=[])

    assert result["stats"] == {"repos": 1, "commits": 7, "persons": 2}


def test_analyst_to_result_orders_persons_by_activity_descending():
    quiet = _make_person("quiet", "Quiet", "q@example.com", as_author=1, as_committer=0)
    busy = _make_person("busy", "Busy", "b@example.com", as_author=8, as_committer=4)
    analyst = _make_analyst(persons=[quiet, busy])

    result = _analyst_to_result(analyst, repo_outcomes=[], notes=[])

    assert [p["key"] for p in result["persons"]] == ["busy", "quiet"]


def test_analyst_to_result_flags_shared_name_used_with_multiple_emails():
    analyst = _make_analyst(name_to_emails={"Alice": {"alice@work.com", "alice@personal.com"}})

    result = _analyst_to_result(analyst, repo_outcomes=[], notes=[])

    assert len(result["shared_name_groups"]) == 1
    assert result["shared_name_groups"][0]["name"] == "Alice"
    assert result["shared_name_groups"][0]["emails"] == ["alice@personal.com", "alice@work.com"]


def test_analyst_to_result_excludes_names_with_a_single_email():
    analyst = _make_analyst(name_to_emails={"Alice": {"alice@example.com"}})

    result = _analyst_to_result(analyst, repo_outcomes=[], notes=[])

    assert result["shared_name_groups"] == []


def test_analyst_to_result_includes_same_person_clusters():
    analyst = _make_analyst(
        same_emails_persons={
            "alice@example.com": (["Alice", "Alice W."], {"alice@example.com", "aw@example.com"}),
        },
    )

    result = _analyst_to_result(analyst, repo_outcomes=[], notes=[])

    assert result["same_person_clusters"] == [
        {"names": ["Alice", "Alice W."], "emails": ["alice@example.com", "aw@example.com"]},
    ]


def test_analyst_to_result_passes_through_repo_outcomes_and_notes_verbatim():
    analyst = _make_analyst()
    repo_outcomes = [{"url": "https://github.com/o/repo", "cloned": False}]
    notes = ["1 of 1 repo(s) failed to clone"]

    result = _analyst_to_result(analyst, repo_outcomes, notes)

    assert result["repos"] == repo_outcomes
    assert result["notes"] == notes


def test_analyst_to_result_wires_mentions_into_matching_persons_only():
    alice = _make_person("alice", "Alice", "alice@example.com")
    bob = _make_person("bob", "Bob", "bob@example.com")
    analyst = _make_analyst(persons=[alice, bob])
    mentions = {
        "alice": {
            "https://github.com/o/repo": {
                "repo_url": "https://github.com/o/repo", "sample_commit": "sha1", "as_author": 1, "as_committer": 0,
            },
        },
    }

    result = _analyst_to_result(analyst, repo_outcomes=[], notes=[], mentions=mentions)

    by_key = {p["key"]: p for p in result["persons"]}
    assert len(by_key["alice"]["mentions"]) == 1
    assert by_key["bob"]["mentions"] == []
