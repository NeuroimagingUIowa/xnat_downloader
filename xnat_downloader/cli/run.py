#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyxnat import Interface
import os
import xmltodict
import logging
from datetime import datetime
import zipfile


def find_scans(ses_dict, scans, scan_dict):
    """
    purpose:

    """
    # {'scan_desc1': ('id', 'label'), 'scan_desc2': ('id', 'label')}
    scan_list = ses_dict['xnat:scans']['xnat:scan']
    xnat_scans = {scan['xnat:series_description']: (scan['@ID']) for scan in scan_list}
    wanted_scan_dict = {scan: type
                        for scan, type in scan_dict.items()
                        if scan_dict[scan][0] in scans}
    download_dict = {scan: (type, xnat_scans[scan])
                     for scan, type in wanted_scan_dict.items()
                     if scan in xnat_scans}
    missing_wanted_scans = list(set(wanted_scan_dict.keys()) - set(download_dict.keys()))
    if missing_wanted_scans:
        for scan in missing_wanted_scans:
            logging.warn('\t\tMissing scan: {}'.format(scan))

    # dictionary with tuples ('func', '700')
    return download_dict


def sort_sessions(sub_dict, ses_labels, sessions):
    """
    purpose:
        sorts the sessions of a subject (by time they were uploaded to xnat)
    inputs:
        sub_dict, a dictionary
        ses_labels, a list
        sessions, a list
    outputs:
        session_info a list with 4 element tuples
        1: dictionary
        2: datetime object
        3: string
        4: string
    """

    ses_list = sub_dict['xnat:Subject']['xnat:experiments']['xnat:experiment']
    # print('check: {}'.format(str(type(ses_list))))
    if type(ses_list) is not list:
        ses_list = [ses_list]
    if ses_labels is None:
        ses_labels = [None]
    # labels the techs give the scans
    session_tech_labels = [ses['@label'] for ses in ses_list]
    upload_date = [get_time(ses) for ses in ses_list]
    # print('upload: {}'.format(upload_date))
    # session_sort = zip(ses_list, upload_date, session_tech_labels)
    # sort by upload time

    session_info = zip(ses_list, upload_date, session_tech_labels, ses_labels)
    # print('session presort: {}'.format(session_info))
    session_info.sort(key=lambda x: x[1])
    # print('session postsort: {}'.format(session_info))

    # print('sessions: {}'.format(sessions))
    if sessions != 'ALL':
        session_info = [tup for tup in session_info if tup[3] in sessions]
    num_sessions = len(sessions)
    # print('session ppostsort: {}'.format(session_info))
    if num_sessions < len(session_info):
        logging.warning('There are more xnat sessions than session labels')
    elif num_sessions > len(session_info):
        logging.warning('There are more session labels than xnat sessions')
    else:
        logging.info('sessions sorted and associated with user label (if any)')

    # 3/4 item tuple: ('ses_dict', 'upload_time', 'tech_label', 'session_label')
    # print('session_info: {}'.format(session_info))
    return session_info


def get_time(session):
    """
    purpose:
        makes a time object
    inputs:
        dictionary
    outputs:
        time object
    """
    date = session['xnat:date']
    time = session['xnat:time']
    xnat_time = datetime.strptime(date+' '+time, '%Y-%m-%d %H:%M:%S')
    return xnat_time


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


def make_bids_dir(subject, sub_vars_dict, scan_type, ses_label, scan, BIDs_num_length, dcm_dir):
    sub_num = str(subject).zfill(BIDs_num_length)
    if sub_vars_dict is not None:
        sub_vars = "".join(sub_vars_dict[str(subject)])
    else:
        sub_vars = ''

    # name of subject directory
    sub_label = sub_vars+sub_num
    if ses_label != 'dummy_session':
        sub_dir = """sub-{subject}/{session}/{scan_type}/
                     sub-{subject}_ses-{session}_{scan}""".format(subject=sub_label,
                                                                  session=ses_label,
                                                                  scan_type=scan_type[0],
                                                                  scan=scan_type[1])
    else:
        sub_dir = """sub-{subject}/{scan_type}/
                     sub-{subject}_{scan}""".format(subject=sub_label,
                                                    scan_type=scan_type[0],
                                                    scan=scan_type[1])

    out_dir = os.path.join(dcm_dir, sub_dir)

    return out_dir


def parse_cmdline():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='download_xnat.py downloads xnat '
                                                 'dicoms and saves them in BIDs '
                                                 'compatible directory format')
    parser.add_argument('-c', '--config', help='login file (contains user/pass info)',
                        default=False)

    # Required arguments
    requiredargs = parser.add_argument_group('Required arguments')
    requiredargs.add_argument('-i', '--input_json',
                              dest='input_json', required=True,
                              help='json file defining inputs for this script.')

    return parser


def main():
    # Start a log file
    logging.basicConfig(filename='xnat_downloader.log', level=logging.DEBUG)
    # Parse the command line options
    opts = parse_cmdline().parse_args()
    # Parse the json spec file
    input_dict = parse_json(opts.input_json)
    # assign variables from the json_file
    project = input_dict['project']
    subjects = input_dict['subjects']
    session_labels = input_dict['session_labels']
    sessions = input_dict['sessions']
    scans = input_dict['scans']
    find_scan_dict = input_dict['scan_dict']
    dcm_dir = input_dict['dcm_dir']
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

    if not BIDs_num_length:
        BIDs_num_length = len(max([str(x) for x in list(subjects)], key=len))

    # log in to the xnat server
    if opts.config:
        central = Interface(config=opts.config)
    else:
        central = Interface(server="https://rpacs.iibi.uiowa.edu/xnat", cachedir='/tmp')

    logging.info('###################################')

    if subjects == 'ALL':
        proj_obj = central.select.project(project)
        subjects = [subject.label() for subject in proj_obj.subjects()]

    for subject in subjects:
        sub_xnat_path = '/project/{project}/subjects/{subject}'.format(subject=subject,
                                                                       project=project)
        sub_obj = central.select(sub_xnat_path)
        if not sub_obj.exists():
            logging.warning('subject {} does not exist, skipping...'.format(subject))
            continue
        logging.info('Started Session Finding For {}'.format(subject))
        # parse xml string into dictionary
        sub_dict = xmltodict.parse(sub_obj.get())
        # get the session information
        sessions_info = sort_sessions(sub_dict, session_labels, sessions)
        for ses_info in sessions_info:
            ses_dict = ses_info[0]
            # ses_time = ses_info[1] # Never used
            ses_tech = ses_info[2]

            if session_labels is not None:
                ses_label = ses_info[3]
            else:
                ses_label = 'dummy_session'

            logging.info("""\ttech label {tech} corresponds
                         to session label {session}""".format(tech=ses_tech,
                                                              session=ses_label))
            logging.info('\tStarting Scan Finding for session {}'.format(ses_label))
            scans_info = find_scans(ses_dict, scans, find_scan_dict)
            for scan in scans_info:
                # two element list ["func", "task-rest"]
                scan_type = scans_info[scan][0]
                # t
                scan_id = scans_info[scan][1]
                logging.info('\t\tStarting Download for scan {}.{}'.format(scan, scan_type))
                scan_xnat_path = os.path.join(sub_xnat_path,
                                              """experiments/
                                                 {label}/
                                                 scans/
                                                 {scan}/
                                                 resources""".format(label=ses_tech,
                                                                     scan=scan_id))
                # presume the first resource is the dicoms
                bids_dir = make_bids_dir(subject,
                                         sub_vars_dict,
                                         scan_type,
                                         ses_label,
                                         scan,
                                         BIDs_num_length,
                                         dcm_dir)

                if not os.path.exists(bids_dir):
                    os.makedirs(bids_dir)

                if os.listdir(bids_dir):
                    logging.warn('\t\tDirectory not empty, skipping download')
                else:
                    print('Downloading {subject}:{session}:{scan}'.format(subject=subject,
                                                                          session=ses_label,
                                                                          scan=scan_type[0]))
                    # download the gif and the dcms
                    # sometimes either the picture (.gif) or dicoms don't exist.
                    for idx in range(len(central.select(scan_xnat_path).get())):
                        central.select(scan_xnat_path)[idx].get(bids_dir)
                        # Log the path where the file was downloaded for ground truth.
                        with open(os.path.join(bids_dir, 'output.txt'), 'w+') as output_file:
                            output_file.write('Data From:\n{}\n'.format(scan_xnat_path))

                        # unzip the downloaded file in the same directory
                        zip_file_name = os.path.join(
                            bids_dir,
                            central.select(scan_xnat_path).get()[idx])+'.zip'

                        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
                        zip_ref.extractall(bids_dir)
                        zip_ref.close()

# just download both and sort them later
# central.select('/project/VOSS_AGING/subjects/9/experiments/RPACS_E19139/scans/1/resources').get()
# ['352584', '352601']

# central.select('/project/VOSS_AGING/subjects/9/experiments/RPACS_E19139/scans/1/resources/352584').get('/home/james')

# TODO
# encode keyword ALL
# filter sessions by user selection


if __name__ == "__main__":
    main()
