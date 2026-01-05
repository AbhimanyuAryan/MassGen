#!/bin/bash
# Wrapper script to run README sync with uv in local environment
# This ensures all dependencies are available from the project's virtualenv

# Check if we're in CI environment
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    # In CI, use python3 directly (dependencies should be installed)
    exec python3 "$(dirname "$0")/precommit_sync_readme.py" "$@"
else
    # Locally, use uv to ensure dependencies are available
    exec uv run python "$(dirname "$0")/precommit_sync_readme.py" "$@"
fi
