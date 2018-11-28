# use neurodebian
FROM neurodebian:trusty

LABEL software='xnat_downloader'
LABEL version="0.2.0"

ARG DEBIAN_FRONTED=noninteractive

# install debian essentials
RUN apt-get update -qq && apt-get install -yq --no-install-recommends  \
    apt-utils \
  	bzip2 \
    ca-certificates \
    curl \
    git \
    unzip \
    pigz

RUN mkdir -p /opt/dcm2niix && \
    cd /opt/dcm2niix && \
    curl -sSLO https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20181125/dcm2niix_25-Nov-2018_lnx.zip && \
    unzip dcm2niix_25-Nov-2018_lnx.zip && \
    rm dcm2niix_25-Nov-2018_lnx.zip

RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh && \
    bash Miniconda2-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda2-latest-Linux-x86_64.sh

ENV PATH=/opt/dcm2niix:/usr/local/miniconda/bin:$PATH \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Copy the code in xnat_downloader to the container
COPY . /opt/xnatDownloader

RUN pip install -r /opt/xnatDownloader/requirements.txt

RUN cd /opt/xnatDownloader && python setup.py install

ENTRYPOINT ["/usr/local/miniconda/bin/xnat_downloader"]
