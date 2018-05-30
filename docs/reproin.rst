.. _reproin:

reproin
=======
This is the reproin heuristic, copied from `heudiconv <https://github.com/nipy/heudiconv/blob/master/heudiconv/heuristics/reproin.py>`_


.. code-block:: console

    (AKA dbic-bids) Flexible heuristic to establish BIDS DataLad datasets hierarchy
    Initially developed and deployed at Dartmouth Brain Imaging Center
    (http://dbic.dartmouth.edu) using Siemens Prisma 3T under the umbrellas of the
    Center of Reproducible Neuroimaging Computation (ReproNim, http://repronim.org)
    and Center for Open Neuroscience (CON, http://centerforopenneuroscience.org).
    ## Dataset ownership/location
    Datasets will be arranged in a hierarchy similar to how study/exam cards are
    arranged at the scanner console.  You should have
    - "region" defined per each PI,
    - on the first level most probably as PI_StudentOrRA/ (e.g., Gobbini_Matteo)
    - StudyID_StudyName/   (e.g. 1002_faceangles)
        - Arbitrary name for the exam card -- it doesn't get into Study Description.
    Selecting specific exam card would populate Study Description field using
    aforementioned levels, which will be used by this heuristic to decide on the
    location of the dataset.
    In case of multiple sessions, it is recommended to generate separate "cards"
    per each session.
    ## Sequence naming on the scanner console
    Sequence names on the scanner must follow this specification to avoid manual
    conversion/handling:
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

