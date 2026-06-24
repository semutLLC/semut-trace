#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <codex-branch|branch-name> [target-branch]" >&2
    exit 2
fi

source_branch="$1"
target_branch="${2:-ai-assisted-trace}"
remote="${REMOTE:-origin}"

if [[ "$source_branch" != codex/* ]]; then
    source_branch="codex/$source_branch"
fi

if [[ "$source_branch" == "$target_branch" ]]; then
    echo "Source and target branches must be different." >&2
    exit 2
fi

git rev-parse --is-inside-work-tree >/dev/null

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Working tree has uncommitted changes. Commit or stash them first." >&2
    exit 1
fi

git fetch "$remote" "$target_branch" "$source_branch"
git switch "$target_branch"
git pull --ff-only "$remote" "$target_branch"
git merge --no-ff "$remote/$source_branch" -m "Merge $source_branch into $target_branch"
git push "$remote" "$target_branch"
git push "$remote" --delete "$source_branch"

if git show-ref --verify --quiet "refs/heads/$source_branch"; then
    git branch -d "$source_branch"
fi

echo "Merged $source_branch into $target_branch and deleted the source branch."
