# xnat_downloader

## Install

```pip install -r requirements.txt```

## Run

```xnat_downloader.py -i <input>.json```

## Formatting the json

The json file specifies what you want to download from xnat as well as where you want to download it to. The keywords in the json file let you customize what values to pass into the xnat_downloader script which will determine what scans get downloaded.

- dcm_dir: The base directory where dicoms will be saved

- project: the project name as it appears on xnat

- subjects: either "ALL" (which will download all available subjects) or a list ([]) that specifies which subjects you want to download (e.g. [1, 4, 60])

- session_labels: "None" if there are not multiple sessions in the study or a list ([]) specifying the order of all the sessions in the study (e.g. ["pre", "post"])

- sessions: "ALL" if you want to download all available sessions, or a list specifying what subset of session_labels you want to download (e.g. ["post"])

- scans: The list of scan types you want to download (e.g. ["anat","func","fmap","dwi"]

- scan_dict: The dictionary linking the series description of the scan set on xnat with the list (see AMBI.json for an example)

