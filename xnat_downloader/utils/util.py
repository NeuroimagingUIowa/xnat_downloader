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
        sub_vars = "".join(sub_vars_dict[subject])
    else:
        sub_vars=''

    # name of subject directory
    sub_label = sub_vars+sub_num
    if ses_label != 'dummy_session':
        sub_dir = 'sub-{subject}/{session}/{scan_type}/sub-{subject}_ses-{session}_{scan}'.format(subject=sub_label, session=ses_label, scan_type=scan_type[0], scan=scan_type[1])
    else:
        sub_dir = 'sub-{subject}/{scan_type}/sub-{subject}_{scan}'.format(subject=sub_label, scan_type=scan_type[0], scan=scan_type[1])

    out_dir = os.path.join(dcm_dir, sub_dir)

    return out_dir
