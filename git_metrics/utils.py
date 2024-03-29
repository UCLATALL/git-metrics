import click
import contextlib
import csv
import git
import os
import subprocess as sp

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser as dateparser
from typing import Iterable, Optional, Union


def assert_git_installed() -> None:
    git_version = sp.check_output(["git", "--version"]).decode("UTF-8")
    assert git_version.startswith("git version"), "You must have git installed."


def recent_commit(branch: git.Head, date: datetime) -> git.Commit:
    repo = branch.repo
    until = date.isoformat()
    sha = repo.git.log(branch, "-1", f"--until={until}", "--format=format:%H")
    if sha == "":
        raise ValueError("No commits were made prior to the given date.")
    return repo.commit(sha)


def resolve_branch(repo: git.Repo, branch: str = "main") -> git.Head:
    try:
        return repo.branches[branch]
    except IndexError as exc:
        if branch == "main":
            with contextlib.suppress(IndexError):
                return repo.branches["master"]
        raise ValueError(f'"{branch}" does not resolve to a valid branch.') from exc


def resolve_commit(repo: git.Repo, commit_ref: str = "main") -> git.Commit:
    try:
        return repo.commit(commit_ref)
    except git.BadName as exc:
        if commit_ref == "main":
            with contextlib.suppress(git.BadName):
                return repo.commit("master")
        raise ValueError(f'"{commit_ref}" does not resolve to a valid commit.') from exc


def date_range(start_date: datetime, end_date: datetime) -> list[datetime]:
    return [
        start_date + relativedelta(days=days)
        for days in range((end_date - start_date).days + 1)
    ]


def parse_date(date: str) -> datetime:
    try:
        return dateparser.parse(date).astimezone()
    except dateparser.ParserError as exc:
        raise ValueError(f'Had trouble with "{date}", try "YYYY-MM-DD" format') from exc


def dt_to_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def parse_int(string: str) -> int:
    return int("".join(filter(str.isdigit, string)))


def write_text(text: str, file: os.PathLike) -> None:
    with open(file, "w") as f:
        f.write(text)


def flatten(nested_list):
    return [item for sub_list in nested_list for item in sub_list]


def create_progress_bar(
    iterable: Optional[Iterable] = None,
    length: Optional[int] = None,
    label: Optional[str] = None,
):
    return click.progressbar(
        iterable, length=length, label=label, empty_char=" ", fill_char="-"
    )


def listdict_to_csv(data: list[dict], file: Union[os.PathLike, click.File]) -> None:
    with contextlib.suppress(TypeError):
        file = open(file, "w")
    write = csv.writer(file, quoting=csv.QUOTE_ALL)
    write.writerow(data[0].keys())
    write.writerows([row.values() for row in data])
    file.close()
