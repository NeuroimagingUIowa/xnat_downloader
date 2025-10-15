# xnat_downloader
[![CircleCI](https://circleci.com/gh/NeuroimagingUIowa/xnat_downloader.svg?style=svg)](https://circleci.com/gh/NeuroimagingUIowa/xnat_downloader)

xnat_downloader downloads dicom data from an xnat server, converts the dicoms to niftis using [dcm2niix](https://github.com/rordenlab/dcm2niix), and saves the output in [BIDS](http://bids.neuroimaging.io/) format. See the [documentation](http://xnat-downloader.readthedocs.io/en/latest/) for details and usage.

## Requirements

- Python 3.9 or newer (tested up through Python 3.13)
- Access to an XNAT instance with the appropriate credentials
- Optional: integration tests require a populated XNAT project that mirrors the historical ``xnatDownload`` dataset. The public ``central.xnat.org`` instance referenced in older versions has been decommissioned.

## Installation (development)

```bash
git clone https://github.com/NeuroimagingUIowa/xnat_downloader.git
cd xnat_downloader
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

After installation you can use the CLI:

```bash
xnat_downloader -i /path/to/config.json
```
