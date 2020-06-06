#!/usr/bin/env bash

generate_docker(){
    docker run kaczmarj/neurodocker:0.7.0 generate docker \
        --base=neurodebian:stretch-non-free \
        --pkg-manager=apt \
        --env LANG=C.UTF-8 \
        --env LC_ALL=C.UTF-8 \
        --install pigz \
        --run "mkdir -p /opt/dcm2niix && \
            cd /opt/dcm2niix && \
            curl -sSLO https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20181125/dcm2niix_25-Nov-2018_lnx.zip && \
            unzip dcm2niix_25-Nov-2018_lnx.zip && \
            rm dcm2niix_25-Nov-2018_lnx.zip" \
        --env 'PATH=/opt/dcm2niix:$PATH' \
        --user=coder \
        --copy . '/home/coder/project' \
        --user=root \
        --run "chown -R coder /home/coder/project" \
        --user=coder \
        --workdir="/home/coder" \
        --env "SHELL=/bin/bash" \
        --miniconda \
            create_env='neuro' \
            conda_install='python=2.7' \
        --run "conda init && . /home/coder/.bashrc && . activate neuro && pip install -e /home/coder/project/" \
        --user=root \
        --entrypoint "xnat_downloader"
}

generate_docker_devel(){
    docker run kaczmarj/neurodocker:0.7.0 generate docker \
    --base=jdkent/xnat_downloader:unstable \
    --pkg-manager=apt \
    --user=coder \
    --workdir="/home/coder" \
    --env "SHELL=/bin/bash" \
    --run "curl -o /tmp/code-server.tar.gz -SL https://github.com/cdr/code-server/releases/download/3.0.2/code-server-3.0.2-linux-x86_64.tar.gz" \
    --run "mkdir -p /opt/codeserver && tar -xvf /tmp/code-server.tar.gz -C /opt/codeserver --strip-components=1" \
    --run '/opt/codeserver/code-server --install-extension eamodio.gitlens && /opt/codeserver/code-server --install-extension ms-python.python' \
    --expose 8080 \
    --entrypoint '/opt/codeserver/code-server --auth none --host 0.0.0.0 /home/coder/project'
}

if [ "$1" == "app" ]; then
    generate_docker
elif [ "$1" == "devel" ]; then
    generate_docker_devel
else
    echo "unknown option"
fi
