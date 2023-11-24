#!/bin/bash
#
# Run mypy separately over components of the project (source, tests)
#
# Call mypy via this script in pre-commit
# - to always check all files (not just those that changed),
# - to check different components of the project separately (in case of multiple packages), and
# - to give mypy access to all dependencies (by running it locally rather than in isolation).
#
# src: https://jaredkhan.com/blog/mypy-pre-commit

set -o errexit

VERBOSE=${VERBOSE:-false}

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}/.."

# Paths relative to project root
paths=(
    src/idpi
    tests/test_idpi
)
for path in "${paths[@]}"; do
    ${VERBOSE} && echo "mypy \"${path}\""
    # https://github.com/python/mypy/issues/7276
    mypy "${path}" --no-incremental || exit
done
