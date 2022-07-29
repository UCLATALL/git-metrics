import click
import csv
import git
import os
import pathlib

from datetime import datetime
from dateutil import parser as dateparser

from .activity import compile
from .similarity import compare
from . import utils as utils


@click.command()
@click.argument("repository", type=str)
@click.argument("start", type=str)
@click.argument("end", type=str)
def similarity(repository: str, start: str, end: str) -> str:
    utils.assert_git_installed()
    repo = get_repo(repository)
    start_commit = get_commit(repo, start)
    end_commit = get_commit(repo, end)
    similarity_index = compare(start_commit, end_commit)
    print_fg = "green" if similarity_index > 65 else "blue"
    click.echo(
        "Repository similarity is ~{}".format(
            click.style(similarity_index, bold=True, fg=print_fg)
        )
    )


@click.command()
@click.argument("repository", type=str)
@click.argument("branch", type=str)
@click.argument("start", type=str)
@click.argument("end", type=str, default=datetime.now().astimezone())
@click.option(
    "--output",
    default="./git-activity.csv",
    prompt="Output file",
    help="The path to the CSV file you want to output to.",
)
def activity(
    repository: str, branch: str, start: str, end: str, output: os.PathLike
) -> str:
    utils.assert_git_installed()
    repo = get_repo(repository)
    branch = get_branch(repo, branch)
    start_date = get_date(start)
    end_date = get_date(end)
    result = compile(branch, start_date, end_date, output)
    click.echo(f'Wrote {len(result)} rows to "{output}"')


def get_repo(repo_path: str) -> git.Repo:
    try:
        repo_path = pathlib.Path(repo_path)
        return git.Repo(repo_path)
    except (git.NoSuchPathError, git.InvalidGitRepositoryError):
        raise ValueError(f'Could not find a valid git repository at "{repo_path}"')


def get_branch(repo: git.Repo, branch: str) -> git.Head:
    try:
        return repo.branches[branch]
    except IndexError:
        raise ValueError(f'Could not find branch "{branch}" in "{repo.working_dir}"')


def get_commit(repo: git.Repo, commit_ref: str) -> git.Commit:
    try:
        return repo.commit(commit_ref)
    except (git.BadName):
        raise ValueError(f'"{commit_ref}" does not resolve to a valid commit.')


def get_date(date: str) -> datetime:
    try:
        return dateparser.parse(date).astimezone()
    except dateparser.ParserError:
        raise ValueError(f'Had trouble with "{date}", try "YYYY-MM-DD" format')
