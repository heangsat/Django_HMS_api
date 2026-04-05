#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This directory is not a Git repository."
  echo "Run: git init"
  exit 1
fi

if [[ ! -d ".githooks" ]]; then
  echo "Missing .githooks directory."
  exit 1
fi

chmod +x .githooks/pre-push
git config core.hooksPath .githooks

echo "Git hooks enabled."
echo "Current hooksPath: $(git config --get core.hooksPath)"
