import git
import os
import subprocess as sp

from datetime import datetime
from dateutil.relativedelta import relativedelta


def assert_git_installed() -> None:
    git_version = sp.check_output(["git", "--version"]).decode("UTF-8")
    assert git_version.startswith("git version"), "You must have git installed."


def recent_commit(branch: git.Head, date: datetime) -> git.Commit:
    repo = branch.repo
    hash = repo.git.log(
        branch, "-1", f"--until={date.isoformat()}", "--format=format:%H"
    )
    return repo.commit(hash)


def resolve_branch(repo: git.Repo, branch: str = "main") -> git.Head:
    try:
        return repo.branches[branch]
    except IndexError:
        if branch == "main":
            try:
                return repo.branches["master"]
            except IndexError:
                pass
        raise ValueError(f'"{branch}" does not resolve to a valid branch.')


def resolve_commit(repo: git.Repo, commit_ref: str = "main") -> git.Commit:
    try:
        return repo.commit(commit_ref)
    except (git.BadName):
        if commit_ref == "main":
            try:
                return repo.commit("master")
            except (git.BadName):
                pass
        raise ValueError(f'"{commit_ref}" does not resolve to a valid commit.')


def date_range(start_date: datetime, end_date: datetime) -> list[datetime]:
    return [
        start_date + relativedelta(days=days)
        for days in range((end_date - start_date).days + 1)
    ]


def dt_to_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def parse_int(string: str) -> int:
    return int("".join(filter(str.isdigit, string)))


def write_text(file: os.PathLike, text: str) -> None:
    with open(file, "w") as f:
        f.write(text)
