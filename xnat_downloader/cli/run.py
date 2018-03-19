#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyxnat import Interface
import os
import xmltodict
import logging
from datetime import datetime
import zipfile


def parse_json(json_file):
    """Parse json file."""
    import json
    with open(json_file) as json_input:
        input_dict = json.load(json_input)
        # print(str(input_dict))
    mandatory_keys = ['scan_dict', 'dcm_dir', 'sessions',
                      'session_labels', 'project', 'subjects', 'scans']
    optional_keys = ['subject_variables_csv', 'zero_pad', 'nii_dir']
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


def read_sub_csv(sub_csv):
    sub_dict = {}
    with open(sub_csv) as sub_file:
        for line in sub_file:
            # mac os specific
            sub_entry = line.strip('\n').split(',')
            sub_dict[sub_entry[0]] = sub_entry[1:]

    return sub_dict


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
    requiredargs = parser.add_argument_group('Required arguments')
    requiredargs.add_argument('-i', '--input_json',
                              dest='input_json', required=True,
                              help='json file defining inputs for this script.')

    return parser


class Subject():
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
    ses: boolean
        True if the subject has sessions.
        False if the subject does not have any sessions
    scan_objs: list
        List of the available scans objects on xnat for a particular session
        (e.g. central.select('project').subject('label').experiment('session').scans.get(''))
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

    def get_sessions(self):
        """
        Retrieves the session objects for the subject
        """
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
            for ses_obj in ses_objs:
                key = ses_obj.attrs.get('label')
                self.ses_dict[key] = ses_obj

    def get_scans(self, ses_obj):
        """
        Retrieves the scan objects for a particular session

        Parameters
        ----------
        ses_obj: object
            session object returned from pyxnat
        """
        if not self.ses or ses_obj.attrs.get('label') not in self.ses_dict.keys():
            print('ERROR: Session {ses} does not exist'.format(ses=ses_obj.attrs.get('label')))
            return 1

        self.scan_objs = list(ses_obj.scans().get(''))
        self.scan_dict = {}
        for scan_obj in scan_objs:
            key = scan_obj.attrs.get('type')
            self.scan_dict[key] = scan_obj

    def download_scan(self, scan, dest):
        """
        Downloads a particular scan session

        Parameters
        ----------

        scan: object
            Scan object returned from pyxnat.
        dest: string
            Directory where the zip file will be saved.
            The actual dicoms will be saved under the general scheme
            <session_label>/scans/<scan_label>/resources/DICOM/files
        """
        from glob import glob
        if scan not in scan_dict.keys():
            print('{scan} is not available for download'.format(scan=scan))
            return 1

        # No easy way to check for complete download
        # the session label (e.g. 20180613)
        # ^soon to be sub-01_ses-01
        ses_dir = scan_dict[scan].parent().label()
        # the number id given to a scan (1, 2, 3, 400, 500)
        scan_id = scan_dict[scan].id()
        # PU:task-rest_bold -> PU_task_rest_bold
        scan_dir = scan_id + '-' + scan.replace('-', '_').replace(':', '_')
        potential_files = glob(os.path.join(dest,
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
            scan_dict[scan].download(dest_dir=dest,
                                     type=scan,
                                     extract=True,
                                     removeZip=True)


def main():
    # Start a log file
    logging.basicConfig(filename='xnat_downloader.log', level=logging.DEBUG)
    # Parse the command line options
    opts = parse_cmdline().parse_args()
    # Parse the json spec file
    input_dict = parse_json(opts.input_json)
    # assign variables from the json_file
    project = input_dict['project']
    subjects = input_dict.get('subjects', 'ALL')
    session_labels = input_dict.get('session_labels', None)
    sessions = input_dict.get('sessions', 'ALL')
    scans = input_dict.get('scans', 'ALL')

    # find_scan_dict = input_dict['scan_dict']
    # dcm_dir = input_dict['dcm_dir']
    # optional entries
    sub_vars = input_dict.get('subject_variables_csv', False)
    BIDs_num_length = input_dict.get('zero_pad', False)
    # nii_dir = input_dict.get('nii_dir', False)  # not sure if this is needed

    if session_labels == "None":
        session_labels = None
    # make the BIDs subject dictionary
    if sub_vars and os.path.isfile(sub_vars):
        sub_vars_dict = read_sub_csv(sub_vars)
    else:
        sub_vars_dict = None

    if not BIDs_num_length and not subjects == "ALL":
        BIDs_num_length = len(max([str(x) for x in list(subjects)], key=len))

    # log in to the xnat server
    if opts.config:
        central = Interface(config=opts.config)
    else:
        central = Interface(server="https://rpacs.iibi.uiowa.edu/xnat", cachedir='/tmp')

    logging.info('###################################')

    proj_obj = central.select.project(project)

    if subjects == "ALL":
        sub_objs = proj_obj.subjects()
        sub_objs._id_header = 'label'
        subjects = sub_objs.get()

    # get all subjects
    subject_dict = {}
    for subject in subjects:
        subject_dict[subject] = Subject(proj_obj, subject)


if __name__ == "__main__":
    main()
