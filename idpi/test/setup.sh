source /project/g110/spack/user/tsa/spack/share/spack/setup-env.sh

cosmo_eccodes_dir=$(spack find --format "{prefix}" cosmo-eccodes-definitions@2.19.0.7%gcc | head -n1)
eccodes_dir=$(spack find --format "{prefix}" eccodes@2.19.0%gcc | head -n1)
export GRIB_DEFINITION_PATH=${cosmo_eccodes_dir}/cosmoDefinitions/definitions/:${eccodes_dir}/share/eccodes/definitions/
SCRIPTPATH="$( cd -- "$(dirname "${BASH_SOURCE[${#BASH_SOURCE[@]} - 1]} ")" >/dev/null 2>&1 ; pwd -P )"
export PYTHONPATH=${SCRIPTPATH}/../src


