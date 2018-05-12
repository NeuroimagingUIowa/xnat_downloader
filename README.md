# xnat_downloader
[![CircleCI](https://circleci.com/gh/HBClab/xnat_downloader.svg?style=svg)](https://circleci.com/gh/HBClab/xnat_downloader)

## Install (within the github directory)

```python setup.py install```

## Run

```xnat_downloader -i <input>.json```

## Formatting the json

The json file specifies what you want to download from xnat as well as where you want to download it to. The keywords in the json file let you customize what values to pass into the xnat_downloader script which will determine what scans get downloaded.

- destination: the base directory to create the BIDS structure

- project: the project name as it appears on xnat

- subjects: (optional) a list ([]) that specifies which subjects you want to download (e.g. [1, 4, 60])

- scans: (optional) The list of scan types you want to download (e.g. ["anat","func","fmap","dwi"]

## The Reproin heuristic
Sequence names on the scanner must follow this specification to avoid manual conversion/handling:

```
  [PREFIX:]<seqtype[-label]>[_ses-<SESID>][_task-<TASKID>][_acq-<ACQLABEL>][_run-<RUNID>][_dir-<DIR>][<more BIDS>][__<custom>]

where

 [PREFIX:] - leading capital letters followed by : are stripped/ignored
 <...> - value to be entered
 [...] - optional -- might be nearly mandatory for some modalities (e.g.,
         run for functional) and very optional for others
 *ID - alpha-numerical identifier (e.g. 01,02, pre, post, pre01) for a run,
       task, session. Note that makes more sense to use numerical values for
       RUNID (e.g., _run-01, _run-02) for obvious sorting and possibly
       descriptive ones for e.g. SESID (_ses-movie, _ses-localizer)
<seqtype[-label]>
   a known BIDS sequence type which is usually a name of the folder under
   subject's directory. And (optional) label is specific per sequence type
   (e.g. typical "bold" for func, or "T1w" for "anat"), which could often
   (but not always) be deduced from DICOM. Known to BIDS modalities are:
     anat - anatomical data.  Might also be collected multiple times across
            runs (e.g. if subject is taken out of magnet etc), so could
            (optionally) have "_run" definition attached. For "standard anat"
            labels, please consult to "8.3 Anatomy imaging data" but most
            common are 'T1w', 'T2w', 'angio'
     func - functional (AKA task, including resting state) data.
            Typically contains multiple runs, and might have multiple different
            tasks different per each run
            (e.g. _task-memory_run-01, _task-oddball_run-02)
     fmap - field maps
     dwi  - diffusion weighted imaging (also can as well have runs)
_ses-<SESID> (optional)
    a session.  Having a single sequence within a study would make that study
    follow "multi-session" layout. A common practice to have a _ses specifier
    within the scout sequence name. You can either specify explicit session
    identifier (SESID) or just say to maintain, create (starts with 1).
    You can also use _ses-{date} in case of scanning phantoms or non-human
    subjects and wanting sessions to be coded by the acquisition date.
_task-<TASKID> (optional)
    a short name for a task performed during that run.  If not provided and it
    is a func sequence, _task-UNKNOWN will be automatically added to comply with
    BIDS. Consult http://www.cognitiveatlas.org/tasks on known tasks.
_acq-<ACQLABEL> (optional)
    a short custom label to distinguish a different set of parameters used for
    acquiring the same modality (e.g. _acq-highres, _acq-lowres  etc)
_run-<RUNID> (optional)
    a (typically functional) run. The same idea as with SESID.
_dir-[AP,PA,LR,RL,VD,DV] (optional)
    to be used for fmap images, whenever a pair of the SE images is collected
    to be used to estimate the fieldmap
<more BIDS> (optional)
    any other fields (e.g. _acq-) from BIDS acquisition
__<custom> (optional)
  after two underscores any arbitrary comment which will not matter to how
  layout in BIDS. But that one theoretically should not be necessary,
  and (ab)use of it would just signal lack of thought while preparing sequence
  name to start with since everything could have been expressed in BIDS fields.
## Last moment checks/FAQ:
- Functional runs should have _task-<TASKID> field defined
- Do not use "+", "_" or "-" within SESID, TASKID, ACQLABEL, RUNID,  so we
  could detect "canceled" runs.
- If run was canceled -- just copy canceled run (with the same index) and re-run
  it. Files with overlapping name will be considered duplicate/canceled session
  and only the last one would remain.  The others would acquire
  __dup0<number>  suffix.
Although we still support "-" and "+" used within SESID and TASKID, their use is
not recommended, thus not listed here
```
