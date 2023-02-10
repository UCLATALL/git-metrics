import git
import io
import os
import pathlib
import subprocess as sp

from tempfile import TemporaryDirectory
from typing import Any, Generator, Optional

from git_metrics import utils


def compare(start: git.Commit, end: git.Commit, glob: str = "*") -> int:
    assert isinstance(start, git.Commit) and isinstance(end, git.Commit)
    script_path = pathlib.Path(__file__).parent / "git-similarity.sh"
    with TemporaryDirectory() as temp_dir:
        git.Repo.init(temp_dir)
        file1 = pathlib.Path(temp_dir) / "start.txt"
        utils.write_text(read_files(start, glob), file1)
        file2 = pathlib.Path(temp_dir) / "end.txt"
        utils.write_text(read_files(end, glob), file2)
        output = sp.check_output([script_path, str(file1), str(file2)], cwd=temp_dir)
        return int(output)


def read_files(commit: git.Commit, glob: str = "*") -> str:
    files = list_git_files(commit, glob)
    texts = [read_git_file(commit, file) for file in files if file is not None]
    return "\n".join(filter(None, texts))


def list_git_files(
    commit: git.Commit,
    glob: str = "*",
    types: Optional[list[str]] = None,
    tree: Optional[git.Tree] = None,
    rel_path: Optional[pathlib.Path] = None,
) -> Generator[pathlib.Path, Any, Any]:
    """List files present in the git tree at a given commit."""
    if types is None:
        types = [".md", ".html", ".js", ".css", ".txt"]
    tree = tree if tree is not None else commit.tree
    working_dir = pathlib.Path(commit.repo.working_dir)
    rel_path = rel_path if rel_path is not None else working_dir
    for blob in tree.blobs:
        maybe_path = rel_path / blob.name
        if maybe_path.match(glob) and (types is None or maybe_path.suffix in types):
            yield maybe_path.relative_to(commit.repo.working_dir)
    for tree in tree.trees:
        yield from list_git_files(commit, glob, types, tree, rel_path / tree.name)


def read_git_file(commit: git.Commit, path: os.PathLike) -> str:
    file = commit.tree / str(path)
    with io.BytesIO(file.data_stream.read()) as contents:
        return contents.read().decode("utf-8")
