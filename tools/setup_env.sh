#!/bin/bash
#
# Create conda environment with pinned or unpinned requirements
#
# - 2022-08 (D. Regenass) Write original script
# - 2022-09 (S. Ruedisuehli) Refactor; add some options
#

# Default env names
DEFAULT_ENV_NAME="idpi"

# Default options
ENV_NAME="${DEFAULT_ENV_NAME}"
PYVERSION=3.10
PINNED=true
EXPORT=false
CONDA=conda
HELP=false

help_msg="Usage: $(basename "${0}") [-n NAME] [-p VER] [-u] [-e] [-m] [-h]

Options:
 -f NAME    Fieldextra Path - defaults to the system one
 -n NAME    Env name [default: ${DEFAULT_ENV_NAME}
 -p VER     Python version [default: ${PYVERSION}]
 -u         Use unpinned requirements (minimal version restrictions)
 -e         Export environment files (requires -u)
 -m         Use mamba instead of conda
 -h         Print this help message and exit
"

# Eval command line options
while getopts f:n:p:ehmu flag; do
    case ${flag} in
        f) FIELDEXTRA_PATH=${OPTARG};;
        n) ENV_NAME=${OPTARG};;
        p) PYVERSION=${OPTARG};;
        e) EXPORT=true;;
        h) HELP=true;;
        m) CONDA=mamba;;
        u) PINNED=false;;
        ?) echo -e "\n${help_msg}" >&2; exit 1;;
    esac
done

if ${HELP}; then
    echo "${help_msg}"
    exit 0
fi

if [ -z ${FIELDEXTRA_PATH+x} ]; then
    echo "IDPI requires a fieldextra binary to be present. The path to the executable needs to be specified  (-f)"
    exit 1
fi

echo "Setting up environment for installation"
eval "$(conda shell.bash hook)" || exit  # NOT ${CONDA} (doesn't work with mamba)
conda activate || exit # NOT ${CONDA} (doesn't work with mamba)

# Create new env; pass -f to overwriting any existing one
echo "Creating ${CONDA} environment"
${CONDA} create -n ${ENV_NAME} python=${PYVERSION} --yes || exit

# Install requirements in new env
if ${PINNED}; then
    echo "Pinned installation"
    ${CONDA} env update --name ${ENV_NAME} --file requirements/environment.yaml || exit
else
    echo "Unpinned installation"
    ${CONDA} env update --name ${ENV_NAME} --file requirements/requirements.yaml || exit
    if ${EXPORT}; then
        echo "Export pinned prod environment"
        ${CONDA} env export --name ${ENV_NAME} --no-builds | \grep -v '^prefix:' > requirements/environment.yaml || exit
    fi
fi

#source conda.sh
conda_dir=`which conda`
miniconda_base="$(dirname $(dirname "$conda_dir"))"
source "${miniconda_base}/etc/profile.d/conda.sh"
conda init bash --no-user --install --system

conda activate ${ENV_NAME}

conda env config vars set FIELDEXTRA_PATH=${FIELDEXTRA_PATH}

cosmo_eccodes=$CONDA_PREFIX/share/eccodes-cosmo-resources
git clone --depth 1 --branch v2.25.0.1 https://github.com/COSMO-ORG/eccodes-cosmo-resources.git $cosmo_eccodes

if [[ -d "$cosmo_eccodes/definitions" ]]; then
    echo 'Cosmo-eccodes-definitions were successfully retrieved.'
else
    echo -e "\e[31mCosmo-eccodes-definitions could not be cloned.\e[0m"
    exit $1
fi
eccodes=$CONDA_PREFIX/share/eccodes

if [[ -d "$eccodes/definitions" ]]; then
    echo 'Eccodes definitions were successfully retrieved.'
else
    echo -e "\e[31mEccodes retrieval failed. \e[0m"
    exit $1
fi

pip install -e .
conda deactivate
