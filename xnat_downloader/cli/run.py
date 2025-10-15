#!/usr/bin/env python3
from pyxnat import Interface
import os
import logging
import re
from subprocess import call
from time import sleep

SCAN_EXPR = """\
^(?P<rec_ex>PU:)?\
(?P<modality>[a-z]+)?\
(-(?P<label>[a-zA-Z0-9]+))?\
(_task-(?P<task>[a-zA-Z0-9]+))?\
(_acq-(?P<acq>[a-zA-Z0-9]+))?\
(_ce-(?P<ce>[a-zA-Z0-9]+))?\
(_rec-(?P<rec>[a-zA-Z0-9]+))?\
(_dir-(?P<dir>[a-zA-Z0-9]+))?\
(_run-(?P<run>[a-zA-Z0-9]+))?\
(_echo-(?P<echo>[0-9]+))?\
"""


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
    destination: string
        Directory to construct the BIDS structure
    project: string
        project ID on xnat that you wish to download from
    num_digits: int
        Explicitly set how many digits you want your subject label to have
        (only useful for entirely numbered subject labels)
    subjects: list
        A list of subjects you wish to download scans from
    scan_dict: dictionary
        a dictionary/hash table where the keys are the scan names on xnat
        and the values are the reproin style scan names
    sub_dict: dictionary
        a dictionary/hash table where the keys are the subject labels on xnat
        and the values are the modified subject labels that you want to be
        displayed
    server: string
        The base URL to the xnat server (e.g. "https://example.xnat.invalid")
    session_labels: list
        (optional) (non-BIDS) If you want to replace the names of the sessions
        on xnat with your own list of scans.
    scan_labels: list
        (optional) a list of the scans you want to download (if you don't want to
        download all the scans).
    Returns
    -------
    input_dict:
        A dictionary containing the parameters specified in the JSON file
    """
    import json
    with open(json_file) as json_input:
        input_dict = json.load(json_input)
        # print(str(input_dict))
    mandatory_keys = ['destination', 'project', 'server']
    optional_keys = ['session_labels', 'subjects', 'scan_labels',
                     'scan_dict', 'num_digits', 'sub_dict', 'sub_label_prefix']
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
    parser.add_argument('--scan-non-fmt', action="store_true",
                        help="if subject and session use BIDS formatting, "
                             "but the scans do not")
    parser.add_argument('--overwrite-nii', action='store_true',
                        help='overwrite the nifti file if it exists')
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
        self.ses_name_dict = None
        self.ses_objs = None
        self.scan_dict = None
        self.scan_objs = None

    def get_sessions(self, labels=None, bids=True):
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

        def organize_sessions(ses_lst, labels):
            from datetime import datetime

            if len(ses_lst) < len(labels):
                msg = """
                      Warning, there are fewer sesses on xnat than there are
                      labels in the json
                      """
                print(msg)
                # shorten label list so that it's the same length
                labels = labels[:len(ses_lst)]

            dateobj_lst = []
            for strdate in ses_lst:
                try:
                    dateobj_lst.append(datetime.strptime(strdate, "%Y%m%d_%H"))
                except ValueError:
                    dateobj_lst.append(datetime.strptime(strdate, "%Y%m%d"))

            # sort the date objects
            dateobj_lst.sort()

            # rewrite the date objects as strings
            strdate_lst = []
            for dateobj in dateobj_lst:
                tmp_str = dateobj.strftime("%Y%m%d_%-H")
                if tmp_str.split('_')[1] == '0':
                    strdate_lst.append(tmp_str.split('_')[0])
                else:
                    strdate_lst.append(tmp_str)
            # example {'20180504_1': 'pre'}
            label_dict = {ses: label for label, ses in zip(labels, strdate_lst)}
            return label_dict

        if not self.sub:
            print('ERROR: no sessions can be found because subject does not exist')
            return 1

        self.ses_objs = list(self.sub_obj.experiments().get(''))
        if not self.ses_objs:
            print('WARNING: No sessions were found')
            self.ses = False
        else:
            self.ses = True
            self.ses_dict = {}
            key_lst = []
            for ses_obj in self.ses_objs:
                # remove "sub-<label>_ses-" from the session label
                # this will not change a session label like 20180506
                key = re.sub(r"^sub-[a-zA-Z0-9]+_ses-", r"", ses_obj.attrs.get('label'))
                # add the session object if we want all sessions or if it matches
                # a string in the labels list.
                if labels is not None:
                    if bids:
                        if key in labels:
                            self.ses_dict[key] = ses_obj
                    else:
                        key_lst.append(ses_obj.attrs.get('label'))
                else:
                    self.ses_dict[key] = ses_obj

            # sort the sessions and apply the labels in the order of the sorted sessions
            # WARNING: this will not work if participant is missing a middle session
            if not bids and labels is not None:
                self.ses_name_dict = organize_sessions(key_lst, labels)
                for ses_obj in self.ses_objs:
                    key = ses_obj.attrs.get('label')
                    if key in self.ses_name_dict.keys():
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

    def download_scan_unformatted(self, scan, dest, scan_repl_dict, bids_num_len,
                                  sub_repl_dict=None, sub_label_prefix=None,
                                  overwrite_nii=False):
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
        bids_num_len: int
            the number of integers to use to represent the subject label
        scan_repl_dict: dict
            Dictionary containing terms to match the scan name on xnat with
            the reproin name of the scan
        sub_label_prefix: string
            prefix to add to the subject label (e.g. "AMBI")
        sub_repl_dict: dict
            dictionary to change the subject label based on its representation on xnat
        overwrite_nii: bool
            overwrite the output nifti file if it already exists
        """
        from glob import glob
        if scan not in self.scan_dict.keys():
            print('{scan} is not available for download'.format(scan=scan))
            return 0

        # No easy way to check for complete download
        # the session label (e.g. 20180613)
        # ^soon to be sub-01_ses-01
        ses_dir = self.scan_dict[scan].parent().label()
        scan_par = self.scan_dict[scan].parent()
        # the number id given to a scan (1, 2, 3, 400, 500)
        scan_id = self.scan_dict[scan].id()
        if scan not in scan_repl_dict.keys():
            print('{scan} not a part of dictionary, skipping'.format(scan=scan))
            return 0

        bids_scan = scan_repl_dict[scan]
        # PU:task-rest_bold -> PU_task_rest_bold
        scan_fmt = re.sub(r'[^\w]', '_', scan)
        scan_dir = scan_id + '-' + scan_fmt

        # Add subject ID folder to path of DICOM download so that sessions are organized by subject -jjs 5/1/2019
        if getattr(self, "label", None) is None:
            dcm_outdir = os.path.join(dest, 'sourcedata')
        else:
            dcm_outdir = os.path.join(dest, 'sourcedata', self.label)

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
            # attempt to download dicoms (with a max of 5 tries)
            max_retries = 5
            for rtry in range(max_retries):
                # track whether download succeeded
                err = False
                try:
                    scan_par.scans().download(dest_dir=dcm_outdir,
                                              type=scan_id,
                                              name=scan_fmt,
                                              extract=True,
                                              removeZip=True)
                except TypeError:
                    print('download attempt {n} failed'.format(n=rtry + 1))
                    err = True
                    sleep(5)
                finally:
                    # break out of for loop if download succeeded
                    if not err:
                        break
                    elif rtry == (max_retries - 1):
                        raise TypeError("Could not download dicom")

        # getting information about the directories
        dcm_dir = os.path.join(dcm_outdir,
                               ses_dir,
                               'scans',
                               scan_dir)
        if sub_repl_dict:
            sub_name = 'sub-' + sub_repl_dict[self.sub_obj.attrs.get('label')]
        else:
            sub_name = 'sub-' + self.sub_obj.attrs.get('label').zfill(bids_num_len)

        if self.ses_name_dict:
            ses_name = 'ses-' + self.ses_name_dict[ses_dir]
        else:
            # To capture cases where the session is named 20180508_2
            ses_name = 'ses-' + ses_dir.replace('_', 's')

        scan_pattern = re.compile(SCAN_EXPR)

        scan_pattern_dict = re.search(scan_pattern, bids_scan).groupdict()
        # check if the modality is empty
        if scan_pattern_dict['modality'] is None:
            print('{scan} is not in BIDS, not converting'.format(scan=scan))
            return 0

        # adding additional information to scan label (such as GE120)
        if sub_label_prefix is not None:
            sub_label = sub_name.split('-')[1]
            sub_name = 'sub-' + sub_label_prefix + sub_label

        # build up the bids directory
        bids_dir = os.path.join(dest, sub_name, ses_name, scan_pattern_dict['modality'])

        if not os.path.isdir(bids_dir):
            os.makedirs(bids_dir)

        # name the bids file
        fname = '_'.join([sub_name, ses_name])

        bids_keys_order = ['task', 'acq', 'ce', 'rec', 'rec_ex', 'dir', 'run', 'echo']

        for key in bids_keys_order:
            label = scan_pattern_dict[key]
            if label is not None:
                if key == 'rec_ex':
                    key = 'rec'
                    label = 'pu'
                fname = '_'.join([fname, key + '-' + label])

        # add the label (e.g. _bold)
        if scan_pattern_dict['label'] is None:
            label = scan_pattern_dict['modality']
        else:
            label = scan_pattern_dict['label']

        fname = '_'.join([fname, label])

        print('the dcm dir is {dcm_dir}'.format(dcm_dir=dcm_dir))
        dcm2niix = 'dcm2niix -o {bids_dir} -f {fname} -z y -b y {dcm_dir}'.format(
            bids_dir=bids_dir,
            fname=fname,
            dcm_dir=dcm_dir)
        bids_outfile = os.path.join(bids_dir, fname + '.nii.gz')
        if not os.path.exists(bids_outfile) or overwrite_nii:
            call(dcm2niix, shell=True)
        else:
            print('It appears the nifti file already exists for {scan}'.format(scan=scan))

    def download_scan(self, scan, dest, sub_label_prefix=None, scan_repl_dict=None,
                      overwrite_nii=False):
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
        sub_label_prefix: string
            Add additional characters to the subject label (e.g. sub-01 -> sub-GE01)
        scan_repl_dict: dict or None
            while subject/session folders on xnat may be named in accordance to BIDS,
            the scan names may not be (e.g. PU: anat-T1w).
            This dictionary converts the scan names to their BIDS formatted counterparts.
            (e.g. "PU: anat-T1w" -> "anat-T1w_rec-pu")
        overwrite_nii: bool
            overwrite the output nifti file if it already exists
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

        if scan_repl_dict:
            if scan not in scan_repl_dict.keys():
                print('{scan} not a part of dictionary, skipping'.format(scan=scan))
                return 0
        # check what the bids scan name "should" be
        if scan_repl_dict:
            bids_scan = scan_repl_dict[scan]
        else:
            bids_scan = scan

        # PU:task-rest_bold -> PU_task_rest_bold
        scan_fmt = re.sub(r'[^\w]', '_', scan)
        scan_dir = scan_id + '-' + scan_fmt

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
            max_retries = 5
            for rtry in range(max_retries):
                # track whether download succeeded
                err = False
                try:
                    scan_par.scans().download(dest_dir=dcm_outdir,
                                              type=scan_id,
                                              name=scan_fmt,
                                              extract=True,
                                              removeZip=True)
                except TypeError:
                    print('download attempt {n} failed'.format(n=rtry + 1))
                    err = True
                    sleep(5)
                finally:
                    # break out of for loop if download succeeded
                    if not err:
                        break
                    elif rtry == (max_retries - 1):
                        raise TypeError("Could not download dicom")

        # getting information about the directories
        dcm_dir = os.path.join(dcm_outdir,
                               ses_dir,
                               'scans',
                               scan_dir)

        sub_ses_pattern = re.compile(r'(sub-[A-Za-z0-9]+)_?(ses-[A-Za-z0-9]+)?')
        sub_name, ses_name = re.search(sub_ses_pattern, ses_dir).groups()

        scan_pattern = re.compile(SCAN_EXPR)

        # WARNING they will only be in the correct order if I am using
        # python3.6+
        scan_pattern_dict = re.search(scan_pattern, bids_scan).groupdict()
        if scan_pattern_dict['modality'] is None:
            print('{scan} is not in BIDS, not converting'.format(scan=scan))
            return 0

        # adding additional information to scan label (such as GE120)
        if sub_label_prefix is not None:
            sub_label = sub_name.split('-')[1]
            sub_name = 'sub-' + sub_label_prefix + sub_label

        # catch the weird case were subjects are not completely deleted from the xnat database,
        # warning: poor fix
        if (
                dest is None or
                sub_name is None or
                ses_name is None or
                scan_pattern_dict['modality'] is None
        ):
            print('assuming {subject} does not exist on xnat, continuing'.format(subject=sub_name))
            return 0

        # build up the bids directory
        bids_dir = os.path.join(dest, sub_name, ses_name, scan_pattern_dict['modality'])

        if not os.path.isdir(bids_dir):
            os.makedirs(bids_dir)

        # name the bids file
        fname = '_'.join([sub_name, ses_name])

        bids_keys_order = ['task', 'acq', 'ce', 'rec', 'rec_ex', 'dir', 'run', 'echo']

        for key in bids_keys_order:
            label = scan_pattern_dict[key]
            if label is not None:
                if key == 'rec_ex':
                    key = 'rec'
                    label = 'pu'
                fname = '_'.join([fname, key + '-' + label])

        # add the label (e.g. _bold)
        if scan_pattern_dict['label'] is None:
            label = scan_pattern_dict['modality']
        else:
            label = scan_pattern_dict['label']

        fname = '_'.join([fname, label])

        dcm2niix = 'dcm2niix -o {bids_dir} -f {fname} -z y -b y {dcm_dir}'.format(
            bids_dir=bids_dir,
            fname=fname,
            dcm_dir=dcm_dir)
        bids_outfile = os.path.join(bids_dir, fname + '.nii.gz')
        if not os.path.exists(bids_outfile) or overwrite_nii:
            call(dcm2niix, shell=True)
        else:
            print('It appears the nifti file already exists for {scan}'.format(scan=scan))


def main():
    """
    Does the main work of calling the functions and class(es) defined to download
    subject dicoms and transfer them to niftis
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
    server = input_dict.get('server', None)
    bids_num_len = input_dict.get('num_digits', False)
    dest = input_dict.get('destination', None)
    scan_repl_dict = input_dict.get('scan_dict', None)
    sub_repl_dict = input_dict.get('sub_dict', None)
    sub_label_prefix = input_dict.get('sub_label_prefix', None)

    if session_labels == "None":
        session_labels = None

    if not bids_num_len and subjects is not None:
        bids_num_len = len(max([str(x) for x in list(subjects)], key=len))

    # log in to the xnat server
    if opts.config:
        central = Interface(config=opts.config)
    else:
        if server is not None:
            central = Interface(server=server)
        else:
            print('Server not specified')
            return 1

    # check if you have access to any projects
    if not central.select.projects().get():
        msg = "You have no access to any projects in the server, " \
              "please check your url, username, and password."
        raise RuntimeError(msg)

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
        if scan_repl_dict and opts.scan_non_fmt:
            sub_class.get_sessions(session_labels)
        elif scan_repl_dict:
            sub_class.get_sessions(session_labels, bids=False)
        else:
            sub_class.get_sessions(session_labels)
        # for every session
        if sub_class.ses:
            for session in sub_class.ses_dict.keys():
                sub_class.get_scans(session, scan_labels)
                # for each available scan
                for scan in sub_class.scan_dict.keys():
                    # download the scan
                    if scan_repl_dict and opts.scan_non_fmt:
                        sub_class.download_scan(scan, dest, sub_label_prefix,
                                                scan_repl_dict, overwrite_nii=opts.overwrite_nii)
                    elif scan_repl_dict:
                        sub_class.download_scan_unformatted(scan, dest, scan_repl_dict,
                                                            bids_num_len, sub_repl_dict,
                                                            sub_label_prefix,
                                                            overwrite_nii=opts.overwrite_nii)
                    else:
                        sub_class.download_scan(scan, dest, sub_label_prefix,
                                                overwrite_nii=opts.overwrite_nii)


if __name__ == "__main__":
    main()
