#!/usr/bin/env bash
SCRIPT_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

PKG_DIR=${SCRIPT_PATH}/../../
if [[ ! -d ${PKG_DIR}/eccodes-cosmo-resources ]]; then
  git clone --depth 1 --branch v2.25.0.1 git@github.com:COSMO-ORG/eccodes-cosmo-resources.git ${PKG_DIR}/eccodes-cosmo-resources 
fi 

if [[ ! -d ${PKG_DIR}/eccodes ]]; then
  git clone --depth 1 --branch 2.25.2 git@github.com:ecmwf/eccodes.git/ ${PKG_DIR}/eccodes
fi 

export GRIB_DEFINITION_PATH=${PKG_DIR}/eccodes-cosmo-resources/definitions/:${PKG_DIR}/eccodes/share/eccodes/definitions/
export PYTHONPATH=${SCRIPT_PATH}/../src


