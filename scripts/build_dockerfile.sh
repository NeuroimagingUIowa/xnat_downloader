#!/usr/bin/env bash

# currently not working since shell is not an option
generate_docker(){
    docker run --rm repronim/neurodocker:2.0.0 generate docker \
        --base-image=neurodebian:bookworm-non-free \
        --pkg-manager=apt \
        --env LANG=C.UTF-8 \
        --env LC_ALL=C.UTF-8 \
        --install pigz \
        --run "mkdir -p /opt/dcm2niix && \
            cd /opt/dcm2niix && \
            curl -sSLO https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20250506/dcm2niix_lnx.zip && \
            unzip dcm2niix_lnx.zip && \
            rm dcm2niix_lnx.zip" \
        --env 'PATH=/opt/dcm2niix:$PATH' \
        --user=coder \
        --copy . '/home/coder/project' \
        --user=root \
        --run "chown -R coder /home/coder/project" \
        --workdir="/home/coder" \
        --env "SHELL=/bin/bash" \
        --env CONDA_PLUGINS_AUTO_ACCEPT_TOS=true \
        --user=root \
        --miniconda \
            method=binaries \
            version=latest \
            env_name=neuro \
            env_exists=false \
            conda_install='python=3.13' \
        --user=coder \
        --run 'echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile' \
        --user=root \
        --run-bash 'source "${CONDA_DIR}/etc/profile.d/conda.sh" && conda activate neuro && pip install --no-cache-dir -e /home/coder/project/[test]' \
        --env 'PATH=/opt/miniconda-latest/envs/neuro/bin:/home/coder/.local/bin:$PATH' \
        --entrypoint "/neurodocker/startup.sh xnat_downloader"
        # --shell "/bin/bash --login -c" \
}

if [ "$1" == "app" ]; then
    generate_docker
else
    echo "unknown option"
fi
