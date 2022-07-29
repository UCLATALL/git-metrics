#! /bin/bash

# git-similarity: script to compute similarity of two files

# Exit with error message 
function die () {
  local message=$1
  [ -z "$message" ] && message="Died"
  echo "$message (at ${BASH_SOURCE[1]}:${FUNCNAME[1]} line ${BASH_LINENO[0]}.)" >&2
  exit 1
}

# Create a tree holding the argument file.
function make_tree () {
  rm -f "$1"
  git add -f "$2" || die "Could not add file to git index"
  git write-tree || die "Could not write git tree"
}

# Print the git similarity of the items
function git_similarity () {
  output=$(git diff-tree -r --name-status --find-renames=01 "$1" "$2")
  
  # should either have one line where the similarity is R### followed by file names
  # (indicating rename and similarity index)
  # or two lines, indicating no similarity (because threshold is 01%)
  case "$output" in
  R*) echo "${output:1:4}";;
  *) echo "000";;
  esac
}

[ $# -ne 2 ] && { echo "Usage: git similarity file1 file2"; exit 1; }
[ -f "$1" ] || die "Cannot find file $1, or not a regular file"
[ -f "$2" ] || die "Cannot find file $2, or not a regular file"

TF=$(mktemp) || die "Failed to create temporary git index"
trap 'rm -f $TF' 0 1 2 3 15
export GIT_INDEX_FILE=$TF

blob1=$(make_tree "$TF" "$1")
blob2=$(make_tree "$TF" "$2")
git_similarity "$blob1" "$blob2"
