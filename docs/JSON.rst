============
JSON file formatting
============

If you want practice to understand the basic format of a json file: see `here <http://jsoneditoronline.org/>`_



The json file specifies what you want to download from xnat as well as where you want to download it to. The keywords in the json file let you customize what values to pass into the xnat_downloader script which will determine what scans get downloaded.

- destination: The base directory where dicoms will be saved

- project: the project name as it appears on xnat

- subjects: (optional) a list ([]) that specifies which subjects you want to download (e.g. [1, 4, 60])

- scans: (optional) The list of scan types you want to download (e.g. ["anat","func","fmap","dwi"]

Below is an example JSON file:

.. code-block:: json

    {
	"destination": "/home/james/Downloads",
	"project": "BIKE_EXTEND",
    }
