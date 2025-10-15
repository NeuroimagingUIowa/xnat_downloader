"""Testing basic functionality for xnat_downloader"""
import fnmatch
import os
import shutil

from ..cli.run import main

def test_cli_bids(monkeypatch):
    import sys

    # set up paths
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    cred = os.path.join(data_dir, 'central.cfg')
    bids_json = os.path.join(data_dir, 'bids_test.json')
    ground_truth_output_file = os.path.join(data_dir, "bids.txt")
    
    with open(ground_truth_output_file, "r") as gt:
        ground_truth_bids_files = {line.rstrip() for line in gt}

    args = [
        "xnat_downloader",
        "-i", bids_json,
        "-c", cred,
    ]

    monkeypatch.setattr(sys, 'argv', args)

    assert main() is None

    # make sure all output files exist
    output_files = []
    for root, dirnames, filenames in os.walk('/tmp/bids'):
        for filename in fnmatch.filter(filenames, "*.*"):
            output_files.append(os.path.join(root, filename))

    output_files_no_prefix = set([file[len('/tmp/bids/'):] for file in output_files])

    assert output_files_no_prefix == ground_truth_bids_files

    # clean up
    shutil.rmtree('/tmp/bids')

    
def test_cli_nonbids(monkeypatch):
    import sys

    # set up paths
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    cred = os.path.join(data_dir, 'central.cfg')
    non_bids_json = os.path.join(data_dir, 'non_bids_test.json')
    ground_truth_output_file = os.path.join(data_dir, "nonbids.txt")
    
    with open(ground_truth_output_file, "r") as gt:
        ground_truth_nonbids_files = {line.rstrip() for line in gt}

    args = [
        "xnat_downloader",
        "-i", non_bids_json,
        "-c", cred,
    ]

    monkeypatch.setattr(sys, 'argv', args)

    assert main() is None

    # make sure all output files exist
    output_files = []
    for root, dirnames, filenames in os.walk('/tmp/nonbids'):
        for filename in fnmatch.filter(filenames, "*.*"):
            output_files.append(os.path.join(root, filename))

    output_files_no_prefix = set([file[len('/tmp/nonbids/'):] for file in output_files])

    assert output_files_no_prefix == ground_truth_nonbids_files

    # clean up
    shutil.rmtree('/tmp/nonbids')
