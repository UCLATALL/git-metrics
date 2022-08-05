import csv
import click
import git
import os
import pathlib

from datetime import datetime
from typing import Tuple

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
@click.option(
    "-s",
    "--start",
    "start",
    required=True,
    multiple=True,
    help="""The date-time to start on (use YYYY-MM-DD). You can supply this option
       multiple times to compute similarities using different start times. The
       resulting CSV will indicate the relevant dates and commits on each row.""",
)
@click.option(
    "-e",
    "--end",
    "end",
    show_default=True,
    default=str(datetime.today().astimezone().date()),
    help="The date-time to end on (use YYYY-MM-DD)",
)
@click.option(
    "-b",
    "--branch",
    "branch",
    show_default=True,
    default="main",
    help="The branch to compare on",
)
@click.option(
    "-o",
    "--output",
    type=click.File(
        "w",
        atomic=True,
    ),
    show_default=True,
    default="./git-similarity.csv",
    prompt="Output file",
    help="The path to the CSV file you want to output to.",
)
@click.option(
    "-y",
    "--yes",
    "overwrite",
    is_flag=True,
    default=False,
    help="Use this option to automatically confirm prompt to overwrite output file",
)
def similarity_across(
    repo: str,
    start: Tuple[str, ...],
    end: str,
    branch: str,
    output: click.File,
    overwrite: bool,
):
    """
    Compute the similarity metric for each day across all days between `--start` and
    `--end`. If multiple start points are given, the similarity is computed by creating
    each start-to-end range and returning the concatenated result. Results are output
    to the CSV specified by `--output`.
    """
    utils.assert_git_installed()
    if pathlib.Path(output.name).expanduser().exists() and not overwrite:
        click.confirm("The output file will be overwritten. Continue?", abort=True)

    repo = get_repo(repo)
    branch = utils.resolve_branch(repo, branch)
    if end is None:
        end = datetime.today().astimezone()
    else:
        end = utils.parse_date(end)

    rows = []
    anchors = [utils.parse_date(date) for date in list(start)]
    comparisons = [utils.date_range(anchor, end) for anchor in anchors]
    with click.progressbar(length=len(utils.flatten(comparisons))) as progress:
        for i, anchor in enumerate(anchors):
            anchor_commit = utils.recent_commit(branch, anchor)
            progress.label = f"Comparing from {str(anchor.date())}"
            for comparison in comparisons[i]:
                comparison_commit = utils.recent_commit(branch, comparison)
                rows.append(
                    {
                        "start_commit": anchor_commit,
                        "end_commit": comparison_commit,
                        "start_date": anchor,
                        "end_date": comparison,
                        "similarity": compare(anchor_commit, comparison_commit),
                    }
                )
                progress.update(1)
        progress.label = "Comparisons complete"

    write = csv.writer(output, quoting=csv.QUOTE_ALL)
    write.writerow(rows[0].keys())
    write.writerows(rows)
    click.echo(f'Wrote {len(rows)} rows to "{output.name}"')


@click.command()
@click.argument("repo", type=str)
@click.argument("branch", type=str)
@click.argument("start", type=str)
@click.argument("end", type=str)
@click.option(
    "-o",
    "--output",
    type=click.File("wb"),
    show_default=True,
    default="./git-activity.csv",
    prompt="Output file",
    help="The path to the CSV file you want to output to.",
)
@click.option(
    "-y",
    "--yes",
    "overwrite",
    is_flag=True,
    default=False,
    help="Use this option to automatically confirm prompt to overwrite output file",
)
def activity(
    repo: str, branch: str, start: str, end: str, output: os.PathLike, overwrite: bool
) -> str:
    """
    Compile metrics of the activity on a git REPO's BRANCH from the START date to the
    END date.
    """
    utils.assert_git_installed()
    if pathlib.Path(output.name).expanduser().exists() and not overwrite:
        click.confirm("The output file will be overwritten. Continue?", abort=True)

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
