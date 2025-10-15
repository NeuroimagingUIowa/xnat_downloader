============
Installation
============

local install
-------------
1. clone the `repository <https://github.com/NeuroimagingUIowa/xnat_downloader>`_ from github

  ``git clone https://github.com/NeuroimagingUIowa/xnat_downloader``

2) within the terminal, cd into the place where you downloaded the repository.
   If you see a setup.py in the directory (use ``ls``),
   then you are in the right place.

  ``cd /path/to/repository/xnat_downloader``

3) Install the repository using Python 3.

  ``python -m pip install --upgrade pip``

  ``python -m pip install -e .``

docker install
--------------
``docker pull jdkent/xnat_downloader``
