# Use Neurodebian
From neurodebian:trusty

MAINTAINER James Kent <james-kent@uiowa.edu>
LABEL software='xnat_downloader'
LABEL version="0.0.1_beta"

ARG DEBIAN_FRONTED=noninteractive

# install debian essentials
RUN apt-get update -qq && apt-get install -yq --no-install-recommends  \
    apt-utils \
  	bzip2 \
    ca-certificates \
    curl \
    git \
    unzip

RUN apt-get update -qq && apt-get install -yq --no-install-recommends  \
    dcm2niix

RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh && \
    bash Miniconda2-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda2-latest-Linux-x86_64.sh

ENV PATH=/usr/local/miniconda/bin:$PATH \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Copy the code in xnat_downloader to the container
COPY . /opt/xnatDownloader

RUN pip install -r /opt/xnatDownloader/requirements.txt

RUN cd /opt/xnatDownloader && python setup.py install

ENTRYPOINT ["/usr/local/miniconda/bin/xnat_downloader"]
