#!/bin/bash

poetry_version="1.8.1"
prefix=$(pwd)/poetry-${poetry_version}

if grep -q balfrin /etc/xthostname; then
    module use /mch-environment/v6/modules/
    module load python/3.10.8
fi

if [ ! -d "${prefix}" ]; then
    echo "Installing poetry in venv at ${prefix}"
    python3 -m venv ${prefix}
    ${prefix}/bin/pip install poetry==${poetry_version}
fi

if [ -d ${HOME}/.local/bin ]; then
    echo "Updating symlink at ${HOME}/.local/bin/poetry"
    ln -sf ${poetry} ${HOME}/.local/bin/poetry
fi

${prefix}/bin/poetry config --list
${prefix}/bin/poetry install -vv --sync

venv=$(${prefix}/bin/poetry run python -c "import sys; print(sys.prefix)")
cosmo_resources=${venv}/share/eccodes-cosmo-resources
if [ ! -d "${cosmo_resources}" ]; then
    git clone --depth 1 --branch v2.25.0.3 https://github.com/COSMO-ORG/eccodes-cosmo-resources.git $cosmo_resources
fi
