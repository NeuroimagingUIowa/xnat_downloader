============
JSON file formatting
============

If you want practice to understand the basic format of a json file: see `here <http://jsoneditoronline.org/>`_



The json file specifies what you want to download from xnat as well as where you want to download it to. The keywords in the json file let you customize what values to pass into the xnat_downloader script which will determine what scans get downloaded.

- dcm_dir: The base directory where dicoms will be saved

- project: the project name as it appears on xnat

- subjects: either "ALL" (which will download all available subjects) or a list ([]) that specifies which subjects you want to download (e.g. [1, 4, 60])

- session_labels: "None" if there are not multiple sessions in the study or a list ([]) specifying the order of all the sessions in the study (e.g. ["pre", "post"])

- sessions: "ALL" if you want to download all available sessions, or a list specifying what subset of session_labels you want to download (e.g. ["post"])

- scans: The list of scan types you want to download (e.g. ["anat","func","fmap","dwi"]

- scan_dict: The dictionary linking the series description of the scan set on xnat with the list (see AMBI.json for an example)

- zero_pad: Specifies how many digits the participant label should have (e.g. 2 corresponds to sub-01, 3 corresponds to 001, etc.)

- subject_variables_csv: A path/file.csv designation where the entries in the first column are the participant labels (not zeropadded), and each subsequent column is a variable you wish to append to the subject label such as group membership (Exp or Con) or some condition (GE or SE).

Below is an example JSON file:

.. code-block:: json

    {
	"dcm_dir": "/home/james/Downloads",
	"project": "VOSS_AGING",
	"subjects": "ALL",
	"session_labels": "None",
	"sessions": "ALL",
	"zero_pad": 3,
	"scans": ["anat","func","fmap","dwi","cbf"],
	"scan_dict" : {
					    "Field Map": ["fmap", "fieldmap"],
					    "PU:fMRI SIMON": ["func", "task-simon_bold"],
					    "PU:fMRI Resting State": ["func", "task-rest_bold"],
					    "DTI - 60 Directions": ["dwi", "dwi"],
					    "3D ASL": ["cbf", "aqc-asl_cbf"],
					    "PU:SAG FSPGR BRAVO": ["anat", "T1w"],
					    "Cerebral Blood Flow": ["cbf", "cbf"]
					}
    }
