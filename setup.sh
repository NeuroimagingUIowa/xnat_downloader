#!/bin/bash 

conda create -n xnat_downloader_env python=2.7
source activate xnat_downloader_env
conda install -c conda-forge dcm2niix
python setup.py

