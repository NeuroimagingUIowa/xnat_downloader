#!/usr/bin/env bash

set -euo pipefail

ENV_NAME=${1:-xnat_downloader_env}

if ! command -v conda >/dev/null 2>&1; then
    echo "Conda is required. Download Miniconda or Miniforge from https://www.anaconda.com/download/ and retry."
    exit 1
fi

# Ensure the current shell session is conda-aware.
eval "$(conda shell.bash hook)"

if ! conda env list | awk '{print $1}' | grep -Fxq "${ENV_NAME}"; then
    conda create -n "${ENV_NAME}" python=3.13 dcm2niix -c conda-forge -y
fi

conda activate "${ENV_NAME}"

python -m pip install --upgrade pip
python -m pip install -e ".[test]"
