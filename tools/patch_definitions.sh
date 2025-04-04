# set up eccodes environment variables
ecr_dir=./.venv/share/eccodes-cosmo-resources
def_dir=$(realpath $ecr_dir)/definitions

# patch eccodes definitions
echo "🔧 Patching eccodes definitions..."
TEMPLATES=("4.0" "4.1" "4.6" "4.8" "4.10" "4.11" "4.41" "4.42")
BASE_URL="https://raw.githubusercontent.com/ecmwf/eccodes/refs/heads/develop/definitions/grib2/templates"
for version in "${TEMPLATES[@]}"; do
    curl -s "${BASE_URL}/template.${version}.def" -o "$def_dir/grib2/template.${version}.def"
done
