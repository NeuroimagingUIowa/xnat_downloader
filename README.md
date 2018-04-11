# xnat_downloader

## Install (within the github directory)

```python setup.py install```

## Run

```xnat_downloader -i <input>.json```

## Formatting the json

The json file specifies what you want to download from xnat as well as where you want to download it to. The keywords in the json file let you customize what values to pass into the xnat_downloader script which will determine what scans get downloaded.

- destination: the base directory to create the BIDS structure

- project: the project name as it appears on xnat

- subjects: (optional) a list ([]) that specifies which subjects you want to download (e.g. [1, 4, 60])

- scans: (optional) The list of scan types you want to download (e.g. ["anat","func","fmap","dwi"]

