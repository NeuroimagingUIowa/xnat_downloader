#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyxnat import Interface
import os
import logging
import re
from subprocess import call


def parse_json(json_file):
    """
    Parse json file.

    Parameters
    ----------
    json_file: json
        JSON file containing information about which subjects/sessions/scans to
        download from which project and where to store the files.

    JSON Keys
    ---------
    destination:
        Directory to construct the BIDS structure
    project:
        project ID on xnat that you wish to download from
    zero_pad:
        Explicitly set how many digits you want your subject label to have
        (only useful for entirely numbered subject labels)
    session_labels:
        A list of session labels wished to be matched on
        (e.g. [pre, post, active, passive])
    subjects:
        A list of subjects you wish to download scans from
    scan_labels:
        The scans you want to download

    Returns
    -------
    input_dict:
        A dictionary containing the parameters specified in the JSON file
    """
    import json
    with open(json_file) as json_input:
        input_dict = json.load(json_input)
        # print(str(input_dict))
    mandatory_keys = ['destination', 'project']
    optional_keys = ['zero_pad', 'session_labels', 'subjects', 'scan_labels']
    total_keys = mandatory_keys+optional_keys
    # print("total_keys: "+str(total_keys))
    # are there any inputs in the json_file that are not supported?
    extra_inputs = list(set(input_dict.keys()) - set(total_keys))
    if extra_inputs:
        logging.warning('JSON spec key(s) not supported: %s' % str(extra_inputs))

    # are there missing mandatory inputs?
    missing_inputs = list(set(mandatory_keys) - set(input_dict.keys()))
    if missing_inputs:
        raise KeyError('option(s) need to be specified in input file: '
                       '%s' % str(missing_inputs))

    return input_dict


def parse_cmdline():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='xnat_downloader downloads xnat '
                                                 'dicoms and saves them in BIDs '
                                                 'compatible directory format')
    parser.add_argument('-c', '--config', help='login file (contains user/pass info)',
                        default=False)
    parser.add_argument('-b', '--bids',
                        help='Assume data are stored in a BIDS-ish format on xnat')
    # Required arguments
    required_args = parser.add_argument_group('Required arguments')
    required_args.add_argument('-i', '--input_json',
                               dest='input_json',
                               help='json file defining inputs for this script.')

    return parser


class Subject:
    """
    Main way to interact with subject data.
    This class represents a single subject's data under a particular project.

    Attributes
    ----------
    sub_obj: object
        The object returned from pyxnat after specifying a subject
        (e.g. central.select('project').subject('label'))
    sub: boolean
        True if the subject object exists.
        False if the subject object does not exist
    ses_objs: list
        List of session objects returned from pyxnat assuming sub_obj was already set.
        (e.g. central.select('project').subject('label').experiments().get(''))
    ses_dict: dictionary
        Dictionary matching the session label with the session object pyxnat gives.
    ses: boolean
        True if the subject has sessions.
        False if the subject does not have any sessions
    scan_objs: list
        List of the available scans objects on xnat for a particular session
        (e.g. central.select('project').subject('label').experiment('session').scans.get(''))
    scan_dict: dictionary
        Dictionary matching a scan type (e.g. PU:T1w) with the scan object (from pyxnat)
    """

    def __init__(self, proj_obj, label):
        """
        Parameters
        ----------
        proj_obj: object
            The object returned from pyxnat after being connected to an xnat
            server and selecting a project (e.g. central.select.project('myProject')).
        label: string
            The label of the participant in the xnat server
            (can be different from the subject ID)
        """
        self.sub_obj = proj_obj.subject(label)
        if not self.sub_obj.exists():
            print("ERROR: Subject does not exist")
            self.sub = False
        else:
            self.sub = True
        # initialize other attributes
        self.ses = False
        self.ses_dict = None
        self.ses_objs = None
        self.scan_dict = None
        self.scan_objs = None

    def get_sessions(self, labels=None):
        """
        Retrieves the session objects for the subject

        Parameters
        ----------
        labels: list | None
            A list of session labels wished to be matched on.
            (e.g. [pre, post, active, passive])

        -- note: This assumes that session names follow the form
                 sub-<label>_ses-<label>, and so the label parameter only represents
                 the <label> after the 'ses-' key
        """
        import re

        if not self.sub:
            print('ERROR: no sessions can be found because subject does not exist')
            return 1

        self.ses_objs = list(self.sub_obj.experiments().get(''))
        if not self.ses_objs:
            print('ERROR: No sessions were found')
            self.ses = False
        else:
            self.ses = True
            self.ses_dict = {}
            for ses_obj in self.ses_objs:
                # remove "sub-<label>_ses-" from the session label
                key = re.sub(r"^sub-[a-zA-Z0-9]+_ses-", r"", ses_obj.attrs.get('label'))
                # add the session object if we want all sessions or if it matches
                # a string in the labels list.
                if labels is None or key in labels:
                    self.ses_dict[key] = ses_obj

    def get_scans(self, ses_label, scan_labels=None):
        """
        Retrieves the scan objects for a particular session

        Parameters
        ----------
        ses_label: string
            session label you want to retrieve the scans from
        scan_labels: list | None
            the scans you want to download
        """
        if not self.ses or ses_label not in self.ses_dict.keys():
            print('ERROR: Session {ses} does not exist'.format(ses=ses_label))
            return 1

        self.scan_objs = list(self.ses_dict[ses_label].scans().get(''))
        self.scan_dict = {}
        for scan_obj in self.scan_objs:
            key = scan_obj.attrs.get('type')
            if scan_labels is None or key in scan_labels:
                self.scan_dict[key] = scan_obj

    def download_scan(self, scan, dest):
        """
        Downloads a particular scan session

        Parameters
        ----------

        scan: string
            Scan object returned from pyxnat.
        dest: string
            Directory where the zip file will be saved.
            The actual dicoms will be saved under the general scheme
            <session_label>/scans/<scan_label>/resources/DICOM/files
        """
        from glob import glob
        if scan not in self.scan_dict.keys():
            print('{scan} is not available for download'.format(scan=scan))
            return 1

        # No easy way to check for complete download
        # the session label (e.g. 20180613)
        # ^soon to be sub-01_ses-01
        ses_dir = self.scan_dict[scan].parent().label()
        scan_par = self.scan_dict[scan].parent()
        # the number id given to a scan (1, 2, 3, 400, 500)
        scan_id = self.scan_dict[scan].id()
        if scan_id == '1' or scan_id == '2':
            print('scan is a localizer or setup scan')
            return 0

        # PU:task-rest_bold -> PU_task_rest_bold
        scan_dir = scan_id + '-' + scan.replace('-', '_').replace(':', '_')

        dcm_outdir = os.path.join(dest, 'sourcedata')
        if not os.path.isdir(dcm_outdir):
            os.makedirs(dcm_outdir)

        potential_files = glob(os.path.join(dcm_outdir,
                                            ses_dir,
                                            'scans',
                                            scan_dir,
                                            'resources/DICOM/files/*.dcm'))
        if potential_files:
            msg = """
                  dicoms were already found in the output directory: {}
                  """.format(potential_files[0])
            print(msg)
        else:
            scan_par.scans().download(dest_dir=dcm_outdir,
                                      type=scan,
                                      extract=True,
                                      removeZip=True)

        # getting information about the directories
        dcm_dir = os.path.join(dcm_outdir,
                               ses_dir,
                               'scans',
                               scan_dir)

        sub_ses_pattern = re.compile(r'(sub-[A-Za-z0-9]+)_?(ses-[A-Za-z0-9]+)?')
        sub_name, ses_name = re.search(sub_ses_pattern, ses_dir).groups()

        scan_pattern = re.compile(r'(PU:)?([a-z]+)(-[a-zA-Z0-9]+)?(_[a-zA-Z0-9_\-]+$)?')

        rec, scan_dir, scan_labelr, scan_info = re.search(scan_pattern, scan).groups()

        # build up the bids directory
        bids_dir = os.path.join(dest, sub_name, ses_name, scan_dir)

        if not os.path.isdir(bids_dir):
            os.makedirs(bids_dir)

        # name the bids file
        fname = '_'.join([sub_name, ses_name])

        if scan_info is not None:
            scan_info = scan_info.lstrip('_')
            fname = '_'.join([fname, scan_info])

        if rec is not None:
            fname = '_'.join([fname, 'rec-pu'])

        if scan_labelr is not None:
            scan_label = scan_labelr.lstrip('-')
        else:
            scan_label = scan_dir

        fname = '_'.join([fname, scan_label])

        dcm2niix = 'dcm2niix -o {bids_dir} -f {fname} -z y -b y {dcm_dir}'.format(bids_dir=bids_dir,
                                                                                  fname=fname,
                                                                                  dcm_dir=dcm_dir)
        bids_outfile = os.path.join(bids_dir, fname)
        if not os.path.exists(bids_outfile):
            call(dcm2niix, shell=True)
        else:
            print('It appears the nifti file already exists for {scan}'.format(scan=scan))


def main():
    """
    Does the main work of calling the functions and class(es) defined to download
    subject dicoms.
    """
    # Start a log file
    logging.basicConfig(filename='xnat_downloader.log', level=logging.DEBUG)
    # Parse the command line options
    opts = parse_cmdline().parse_args()
    # Parse the json spec file
    input_dict = parse_json(opts.input_json)
    # assign variables from the json_file
    project = input_dict['project']
    subjects = input_dict.get('subjects', None)
    session_labels = input_dict.get('session_labels', None)
    scan_labels = input_dict.get('scan_labels', None)
    bids_num_len = input_dict.get('zero_pad', False)
    dest = input_dict.get('destination', None)
    # nii_dir = input_dict.get('nii_dir', False)  # not sure if this is needed

    if session_labels == "None":
        session_labels = None

    if not bids_num_len and subjects is not None:
        bids_num_len = len(max([str(x) for x in list(subjects)], key=len))

    # log in to the xnat server
    if opts.config:
        central = Interface(config=opts.config)
    else:
        central = Interface(server="https://rpacs.iibi.uiowa.edu/xnat", cachedir='/tmp')

    logging.info('###################################')

    proj_obj = central.select.project(project)
    if subjects is None:
        sub_objs = proj_obj.subjects()
        # list the subjects by their label (e.g. sub-myname)
        # instead of the RPACS_1223 ID given to them
        sub_objs._id_header = 'label'
        subjects = sub_objs.get()

    # get all subjects
    subject_dict = {}
    for subject in subjects:
        subject_dict[subject] = Subject(proj_obj, subject)
        sub_class = subject_dict[subject]
        # get the session objects
        sub_class.get_sessions(session_labels)
        # for every session
        for session in sub_class.ses_dict.keys():
            sub_class.get_scans(session, scan_labels)
            # for each available scan
            for scan in sub_class.scan_dict.keys():
                # download the scan
                sub_class.download_scan(scan, dest)


if __name__ == "__main__":
    main()
