import os
import subprocess as sp

from datetime import datetime
from dateutil.relativedelta import relativedelta


def assert_git_installed() -> None:
    git_version = sp.check_output(["git", "--version"]).decode("UTF-8")
    assert git_version.startswith("git version"), "You must have git installed."


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
