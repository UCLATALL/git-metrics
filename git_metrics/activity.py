import csv
import git
import os
import tqdm

from datetime import datetime
from dateutil import parser as dateparser
from typing import Optional, Union

from . import utils as utils


def compile(
    branch: git.Head,
    start_date: Union[str, datetime],
    end_date: Optional[Union[str, datetime]] = datetime.now().astimezone(),
    output: Optional[os.PathLike] = None,
) -> list[dict]:
    if not isinstance(start_date, datetime):
        start_date = dateparser.parse(start_date).astimezone()
    if not isinstance(end_date, datetime):
        end_date = dateparser.parse(start_date).astimezone()
    activity = git_activity(branch, start_date, end_date)
    if output is not None:
        with open(output, "w") as file:
            write = csv.writer(file, quoting=csv.QUOTE_ALL)
            write.writerow(activity[0].keys())
            write.writerows([row.values() for row in activity])
    return activity


def git_activity(
    branch: git.Head, start_date: datetime, end_date: datetime
) -> list[dict]:
    rows = []
    current_date = start_date
    date_range = utils.date_range(start_date, end_date)
    date_iterator = tqdm.tqdm(date_range[1:], "Compiling git activity")
    for next_date in date_iterator:
        commits, stats = log_data(branch, current_date, next_date)
        _, insertions, deletions = summarize_stats(stats)
        authors = [commit.author for commit in commits]
        rows.append(
            {
                "date": utils.dt_to_str(next_date),
                "n_commits": len(commits),
                "n_authors": len(set(authors)),
                "n_insertions": insertions,
                "n_deletions": deletions,
            }
        )
        current_date = next_date
    return rows


def log_data(
    branch: git.Head, since: datetime, until: datetime
) -> tuple[list[git.Commit], list[str]]:
    data_str: str = branch.repo.git.log(
        branch,
        f"--since={since}",
        f"--until={until}",
        "--no-merges",
        "--format=format:%H",
        "--shortstat",
    )
    data_lines = [text.strip() for text in data_str.splitlines() if text]
    hashes = [line for line in data_lines if " " not in line]
    stats = [line for line in data_lines if " " in line]
    commits = [branch.repo.commit(hash) for hash in hashes]
    return (commits, stats)


def summarize_stats(stats: list[str]) -> tuple[int, int, int]:
    changed = 0
    insertions = 0
    deletions = 0
    for stat in stats:
        parts = stat.split(",")
        for part in parts:
            if "changed" in part:
                changed += utils.parse_int(part)
            elif "insert" in part:
                insertions += utils.parse_int(part)
            else:
                deletions += utils.parse_int(part)
    return (changed, insertions, deletions)
