#!/bin/bash

poetry_version="1.8.1"
prefix=$(pwd)/poetry-${poetry_version}

if [ ! -d "${prefix}" ]; then
    echo "Installing poetry in venv at ${prefix}"
    python3 -m venv ${prefix}
    ${prefix}/bin/pip install poetry==${poetry_version}
fi

if [ -d ${HOME}/.local/bin ]; then
    echo "Updating symlink at ${HOME}/.local/bin/poetry"
    ln -sf ${prefix}/bin/poetry ${HOME}/.local/bin/poetry
fi

${prefix}/bin/poetry config --list
${prefix}/bin/poetry install -vv --all-extras
