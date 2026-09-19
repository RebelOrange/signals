#!/usr/bin/env bash
set -e

# Configuration variables
YAML_FILE="dsp_env.yml"     # Path to your environment YAML file
NEW_ENV="dsp"               # Name for the target Conda environment
UHD_REPO_DIR="/opt/rfdev-envs/workarea/uhd"        # Path where UHD source code will be cloned

# Initialize Conda inside non-interactive shell
eval "$(conda shell.bash hook)"

echo "=== 1. Creating Conda environment from $YAML_FILE ==="
if conda env list | grep -qE "^${NEW_ENV}\s"; then
    echo "Environment '$NEW_ENV' already exists. Updating environment..."
    conda env update -n "$NEW_ENV" -f dsp_env.yml --prune
else
    echo "Environment '$NEW_ENV' does not exist. Creating environment..."
    conda env create -n "$NEW_ENV" -f dsp_env.yml
fi
conda activate "$NEW_ENV"

echo "=== 2. Ensuring build toolchain dependencies exist in $NEW_ENV ==="
# Installs missing compilation tools into the environment if not already in environment.ymlu

echo "=== 3. Pulling UHD master branch ==="
if [ ! -d "$UHD_REPO_DIR" ]; then
    git clone https://github.com/EttusResearch/uhd.git "$UHD_REPO_DIR"
fi

cd "$UHD_REPO_DIR"
git checkout master
git pull origin master

echo "=== 4. Building and installing UHD into $CONDA_PREFIX ==="
mkdir -p host/build
cd host/build

cmake -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" \
      -DPYTHON_EXECUTABLE="$CONDA_PREFIX/bin/python" \
      -DENABLE_TESTS=OFF \
      -DENABLE_EXAMPLES=ON \
      ../

make -j$(nproc)
make install