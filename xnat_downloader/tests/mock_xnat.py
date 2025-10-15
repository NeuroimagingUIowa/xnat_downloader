"""Lightweight mock objects emulating a subset of the pyxnat API for testing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional


MOCK_DATA: Dict[str, Dict] = {
    "projects": {
        "xnatDownload": {
            "subjects": {
                "sub-001": {
                    "label": "sub-001",
                    "sessions": [
                        {
                            "original_label": "sub-001_ses-01",
                            "scans": [
                                {
                                    "id": "1",
                                    "type": "anat-T1w",
                                    "dicom_files": ["T1w_001.dcm"],
                                },
                                {
                                    "id": "2",
                                    "type": "func-bold_task-rest_run-01",
                                    "dicom_files": ["rest_001.dcm"],
                                },
                            ],
                        }
                    ],
                },
                "21": {
                    "label": "21",
                    "sessions": [
                        {
                            "original_label": "20180101",
                            "scans": [
                                {
                                    "id": "1",
                                    "type": "SAG FSPGR BRAVO",
                                    "dicom_files": ["pre_T1w.dcm"],
                                }
                            ],
                        },
                        {
                            "original_label": "20180202",
                            "scans": [
                                {
                                    "id": "2",
                                    "type": "DTI",
                                    "dicom_files": ["post_dti.dcm"],
                                }
                            ],
                        },
                        {
                            "original_label": "20180303",
                            "scans": [
                                {
                                    "id": "3",
                                    "type": "fMRI Resting State",
                                    "dicom_files": ["checkup_rest.dcm"],
                                }
                            ],
                        },
                    ],
                },
            }
        }
    }
}


class MockInterface:
    """Replacement for :class:`pyxnat.Interface` used in the unit tests."""

    def __init__(self, config: Optional[str] = None, server: Optional[str] = None):
        if config:
            with open(config, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            self.server = cfg.get("server")
        else:
            self.server = server

        if not self.server:
            raise ValueError("Server URL must be provided for the mock interface.")

        self._data = MOCK_DATA
        self.select = MockSelect(self._data)


class MockSelect:
    def __init__(self, data: Dict[str, Dict]):
        self._data = data

    def projects(self) -> "MockProjects":
        return MockProjects(self._data["projects"])

    def project(self, project_label: str) -> "MockProject":
        project_data = self._data["projects"].get(project_label)
        if project_data is None:
            raise KeyError(f"Unknown project: {project_label}")
        return MockProject(project_label, project_data)


class MockProjects:
    def __init__(self, projects: Dict[str, Dict]):
        self._projects = projects

    def get(self) -> List[str]:
        return list(self._projects.keys())


class MockProject:
    def __init__(self, project_id: str, project_data: Dict):
        self.project_id = project_id
        self.data = project_data

    def subjects(self) -> "MockSubjects":
        return MockSubjects(self.data["subjects"])

    def subject(self, label: str) -> "MockSubject":
        subject_data = self.data["subjects"].get(label)
        return MockSubject(label, subject_data)


class MockSubjects:
    def __init__(self, subjects: Dict[str, Dict]):
        self._subjects = subjects
        self._id_header = "id"

    def get(self) -> List[str]:
        return list(self._subjects.keys())


class MockSubject:
    def __init__(self, label: str, subject_data: Optional[Dict]):
        self._label = label
        self._data = subject_data
        self.attrs = {"label": subject_data["label"]} if subject_data else {}

    def exists(self) -> bool:
        return self._data is not None

    def experiments(self) -> "MockExperiments":
        sessions = self._data.get("sessions", []) if self._data else []
        return MockExperiments(self, sessions)


class MockExperiments:
    def __init__(self, subject: MockSubject, sessions: Iterable[Dict]):
        self.subject = subject
        self.sessions_data = list(sessions)

    def get(self, _selector: str = "") -> List["MockSession"]:
        return [
            MockSession(self.subject, session_data) for session_data in self.sessions_data
        ]


class MockSession:
    def __init__(self, subject: MockSubject, session_data: Dict):
        self.subject = subject
        self.original_label = session_data["original_label"]
        self.attrs = {"label": self.original_label}
        self._scans = [
            MockScan(self, scan_data["id"], scan_data["type"], scan_data["dicom_files"])
            for scan_data in session_data.get("scans", [])
        ]
        self._scans_by_id = {scan.id(): scan for scan in self._scans}

    def label(self) -> str:
        return self.original_label

    def scans(self) -> "MockScansCollection":
        return MockScansCollection(self)


class MockScansCollection:
    def __init__(self, session: MockSession):
        self.session = session

    def get(self, _selector: str = "") -> List["MockScan"]:
        return list(self.session._scans)

    def download(
        self,
        dest_dir: str,
        type: str,
        name: str,
        extract: bool = True,
        removeZip: bool = True,
    ) -> None:
        scan = self.session._scans_by_id[str(type)]
        base = (
            Path(dest_dir)
            / self.session.label()
            / "scans"
            / f"{type}-{name}"
            / "resources"
            / "DICOM"
            / "files"
        )
        base.mkdir(parents=True, exist_ok=True)
        for filename in scan.dicom_files:
            (base / filename).write_text("mock dicom data", encoding="utf-8")


class MockScan:
    def __init__(self, session: MockSession, scan_id: str, scan_type: str, dicom_files: List[str]):
        self._session = session
        self._id = str(scan_id)
        self.scan_type = scan_type
        self.dicom_files = dicom_files
        self.attrs = {"type": scan_type}

    def id(self) -> str:
        return self._id

    def parent(self) -> MockSession:
        return self._session

