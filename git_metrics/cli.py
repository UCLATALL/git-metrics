import click
import git
import os
import pathlib

from .activity import compile
from .similarity import compare
from . import utils as utils


@click.command()
@click.argument("repo", type=str)
@click.argument("start", type=str)
@click.argument("end", type=str)
@click.option(
    "-d",
    "--dates",
    "dates",
    is_flag=True,
    show_default=True,
    default=False,
    help="Flag to interpret `START`/`END` as dates instead of commits",
)
@click.option(
    "-b",
    "--branch",
    "branch",
    show_default=True,
    default="main",
    help="If using `--dates`, the branch to compare on",
)
def similarity(
    repo: str, start: str, end: str, dates: bool = False, branch: str = "main"
) -> str:
    """
    Calculate the similarity of the content of a git REPO (specified by passing the
    path to the repo) by comparing the state at the START commit reference against
    the state at the END commit reference. Commit references can be given as commit
    hashes or really anything `git rev-parse` can handle.
    """
    utils.assert_git_installed()
    repo = get_repo(repo)

    if not dates:
        start_commit = utils.resolve_commit(repo, start)
        end_commit = utils.resolve_commit(repo, end)
    else:
        branch = utils.resolve_commit(repo, branch)
        start_commit = utils.recent_commit(branch, utils.parse_date(start))
        end_commit = utils.recent_commit(branch, utils.parse_date(end))

    similarity_index = compare(start_commit, end_commit)
    print_fg = "green" if similarity_index > 65 else "blue"
    click.echo(
        "Repository similarity is ~{}".format(
            click.style(similarity_index, bold=True, fg=print_fg)
        )
    )


@click.command()
@click.argument("repo", type=str)
@click.argument("branch", type=str)
@click.argument("start", type=str)
@click.argument("end", type=str)
@click.option(
    "-o",
    "--output",
    type=click.File("wb"),
    default="./git-activity.csv",
    prompt="Output file",
    help="The path to the CSV file you want to output to.",
)
def activity(repo: str, branch: str, start: str, end: str, output: os.PathLike) -> str:
    """
    Compile metrics of the activity on a git REPO's BRANCH from the START date to the
    END date.
    """
    utils.assert_git_installed()
    repo = get_repo(repo)
    branch = utils.resolve_branch(repo, branch)
    start_date = utils.parse_date(start)
    end_date = utils.parse_date(end)
    result = compile(branch, start_date, end_date, output)
    click.echo(f'Wrote {len(result)} rows to "{output}"')


def get_repo(repo_path: str) -> git.Repo:
    try:
        repo_path = pathlib.Path(repo_path)
        return git.Repo(repo_path)
    except (git.NoSuchPathError, git.InvalidGitRepositoryError):
        raise ValueError(f'Could not find a valid git repository at "{repo_path}"')
