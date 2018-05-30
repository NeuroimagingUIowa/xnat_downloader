============
Usage
============
.. code-block:: console

    usage: xnat_downloader [-h] [-c CONFIG] [-i INPUT_JSON]

    xnat_downloader downloads xnat dicoms and saves them in BIDs compatible
    directory format

    optional arguments:
    -h, --help  show this help message and exit
    -c CONFIG, --config CONFIG  login file (contains user/pass info)

    Required arguments:
    -i INPUT_JSON, --input_json INPUT_JSON  json file defining inputs for this script.

json format
-------------------
The json file has multiple fields specifying where and how
the data are downloaded from xnat.

* **destination**: string
    (required) The absolute path to the
    output base directory of the BIDS dataset
* **project**: string
    (required) The name of the project on xnat
* **server**: string
    (required) The base URL to the xnat server (e.g. "https://central.xnat.org")
* **subjects**: list
    (optional) The subjects you wish to download from xnat.
    Use the subject names as they are seen on xnat.
* **sub_dict**: dictionary
    (optional) (non-BIDS) If you want to change the subject label
    that is not represented in the xnat subject name
* **session_labels**: list
    (optional) (non-BIDS) If you want to replace the names of the sessions
    on xnat with your own list of scans.

    .. warning:: this will not behave as expected if the subject on xnat
                 has a missing "middle" session or an extra session.
* **scan_labels**: list
    (optional) a list of the scans you want to download (if you don't want to
    download all the scans).
* **num_digits**: int
    (optional) an integer indicating how many digits the subject number should
    have. For example if the subject number on xnat is 10, then setting
    `num_digits` to 2 will not change the subject 10, but if `num_digits` was
    set to 3 then subject 10 will be written as 010.
* **scan_dict**: dictionary
    (conditionally required) (non-BIDS) required if your dicoms are not stored
    in a BIDS format on xnat. The keys to the dictionary are
    scan names as they are seen on xnat (e.g. "SAG FSPGR BRAVO"),
    and the values are the associated :ref:`reproin` (BIDS-ish)
    name for the scan (e.g. "anat-T1w").

example json
************
.. literalinclude:: ../tests/non_bids_test.json

Once installed and the json file is configured,
the final step is to call the command.

**locally installed:** (python2 only)

.. code-block:: console

    xnat_downloader -i /path/to/json/file.json

**via docker:**

.. code-block:: console

    docker run \
    -v /path/to/out:/out \
    -v /path/to/json/:/json \
    jdkent:xnat_downloader \
    -i /json/file.json

**Note**: when calling via docker,
the destination location should be specified
relative to where the path is in the docker
container, not on your machine.
