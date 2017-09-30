def find_scans(ses_dict, scans, scan_dict):
    """
    purpose:

    """
    # {'scan_desc1': ('id', 'label'), 'scan_desc2': ('id', 'label')}
    scan_list = ses_dict['xnat:scans']['xnat:scan']
    xnat_scans = {scan['xnat:series_description']: (scan['@ID']) for scan in scan_list}
    wanted_scan_dict = {scan: type for scan, type in scan_dict.items() if scan_dict[scan][0] in scans}
    download_dict = {scan: (type, xnat_scans[scan]) for scan, type in wanted_scan_dict.items() if scan in xnat_scans}
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
        ses_list=[ses_list]
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
