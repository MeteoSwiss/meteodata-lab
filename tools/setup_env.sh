#!/usr/bin/env bash


if command -v spack &> /dev/null
then
    echo "⏩ Spack already configured, skipping setup."
else
    echo "🚀 Installing Spack..."
    spack_c2sm_url=https://github.com/C2SM/spack-c2sm.git
    spack_c2sm_tag=v0.21.1.3
    spack_c2sm_dir=${HOME}/spack-c2sm

    if [ -d ${spack_c2sm_dir} ]; then
        echo "⏩ Spack repo exists in ${spack_c2sm_dir}, skipping setup"
    else
        echo "🧱 Cloning spack-c2sm from ${spack_c2sm_url} into ${spack_c2sm_dir}"
        git clone --depth 1 --recurse-submodules -b ${spack_c2sm_tag} ${spack_c2sm_url} ${spack_c2sm_dir}
    fi

    # puts spack command in PATH, sets up MODULEPATH, bash tab completion, etc.
    echo "📦 Setting up Spack on ${hostname}..."
    . ${spack_c2sm_dir}/setup-env.sh &> /dev/null
fi


if [ -z "$SPACK_ENV" ]; then
    echo "📦 Activating and installing Spack environment..."
    spack env activate -p ./spack-env

    # write log to a file
    spack install --no-check-signature --no-checksum &> /dev/null
fi

if ! command -v poetry > /dev/null; then
    echo "❌ Poetry not found, please install it."
    return 1
fi

venv_dir=$(realpath .venv)
echo "📦 Syncing python dependencies for venv in ${venv_dir}"
# NOTE: important! Eccodes python bindings must be installed
# without the binary package, otherwise it will conflict with the
# installation in the spack environment.
poetry config --local installer.no-binary eccodes
poetry install &> /dev/null


clone_dir=$(realpath ./.venv/share/eccodes-cosmo-resources)
if [ ! -d "$clone_dir" ]; then
    echo "🌐 Cloning eccodes-cosmo-resources to ${clone_dir}"
    git clone git@github.com:COSMO-ORG/eccodes-cosmo-resources -b v2.35.0.1 $clone_dir &> /dev/null
else
    echo "⏩ eccodes-cosmo-resources already cloned to ${clone_dir}, skipping."
fi

# resolve path from relative to this file
echo "📚 Setting up ECCODES environment variables..."
export ECCODES_DIR=$(realpath ./spack-env/.spack-env/view)

echo
echo "✅ Environment ready!"
