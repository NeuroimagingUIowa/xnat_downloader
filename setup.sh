#!/bin/bash 

if [ -z $(which conda) ]; then
    echo "please install anaconda, see here: https://www.anaconda.com/download/"
    exit 1
fi
conda create -n xnat_downloader_env python=2.7 dcm2niix -c conda-forge -y
python setup.py install

