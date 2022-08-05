import click
import git
import pathlib

from datetime import datetime
from typing import Tuple

from .activity import compile_activity
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
    show_default=False,
    default=str(datetime.today().astimezone().date()),
    help="The date-time to end on (use YYYY-MM-DD) [default: today]",
)
@click.option(
    "-b",
    "--branch",
    "branch",
    show_default=True,
    default="main",
    help="The branch of interest",
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
    check_output(output, overwrite)
    repo = get_repo(repo)
    branch = utils.resolve_branch(repo, branch)
    end = datetime.today().astimezone() if end is None else utils.parse_date(end)

    rows = []
    anchors = [utils.parse_date(date) for date in list(start)]
    comparisons = [utils.date_range(anchor, end) for anchor in anchors]
    with utils.create_progress_bar(
        length=len(utils.flatten(comparisons)), label="Computing similarity"
    ) as progress:
        for i, anchor in enumerate(anchors):
            anchor_commit = utils.recent_commit(branch, anchor)
            for comparison in comparisons[i]:
                comparison_commit = utils.recent_commit(branch, comparison)
                similarity = compare(anchor_commit, comparison_commit)
                progress.update(1)
                rows.append(
                    {
                        "start_commit": anchor_commit,
                        "end_commit": comparison_commit,
                        "start_date": anchor,
                        "end_date": comparison,
                        "similarity": similarity,
                    }
                )
    utils.listdict_to_csv(rows, output)
    click.echo(f'Wrote {len(rows)} rows to "{output.name}"')


@click.command()
@click.argument("repo", type=str)
@click.argument("start", type=str)
@click.option(
    "-e",
    "--end",
    "end",
    show_default=False,
    default=str(datetime.today().astimezone().date()),
    help="The date-time to end on (use YYYY-MM-DD) [default: today]",
)
@click.option(
    "-b",
    "--branch",
    "branch",
    show_default=True,
    default="main",
    help="The branch of interest",
)
@click.option(
    "-o",
    "--output",
    type=click.File(
        "w",
        atomic=True,
    ),
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
    repo: str, branch: str, start: str, end: str, output: click.File, overwrite: bool
) -> str:
    """
    Compile metrics of the activity on a git REPO's BRANCH from the START date to the
    `--end` date.
    """
    utils.assert_git_installed()
    check_output(output, overwrite)
    repo = get_repo(repo)
    branch = utils.resolve_branch(repo, branch)
    start_date = utils.parse_date(start)
    end_date = utils.parse_date(end)

    activity = compile_activity(branch, start_date, end_date)
    utils.listdict_to_csv(activity, output)
    click.echo(f'Wrote {len(activity)} rows to "{output.name}"')


def get_repo(repo_path: str) -> git.Repo:
    try:
        repo_path = pathlib.Path(repo_path)
        return git.Repo(repo_path)
    except (git.NoSuchPathError, git.InvalidGitRepositoryError):
        raise ValueError(f'Could not find a valid git repository at "{repo_path}"')


def check_output(output: click.File, overwrite: bool):
    output_path = pathlib.Path(output.name).expanduser()
    if output_path.is_dir():
        click.echo(
            (
                f'The output path "{output.name}" resolves to a directory.\n'
                "You probably don't want to overwrite a full directory..."
            )
        )
        raise click.Abort()
    if output_path.exists() and not overwrite:
        click.confirm("The output file will be overwritten. Continue?", abort=True)
    if not output_path.parent.is_dir():
        output_path.parent.mkdir(parents=True)
        click.echo(f'Created output directory "{output_path.parent}"')
