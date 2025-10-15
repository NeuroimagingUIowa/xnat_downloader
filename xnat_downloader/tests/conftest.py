from __future__ import annotations

from pathlib import Path

import pytest

from .mock_xnat import MockInterface


@pytest.fixture(autouse=True)
def mock_xnat_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch external dependencies so tests run against an in-memory XNAT."""
    from xnat_downloader.cli import run

    monkeypatch.setattr(run, "Interface", MockInterface)

    def fake_dcm2niix(command: str, shell: bool = True) -> int:
        parts = command.split()
        out_dir = Path(parts[parts.index("-o") + 1])
        fname = parts[parts.index("-f") + 1]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{fname}.nii.gz").write_text("mock nifti", encoding="utf-8")
        (out_dir / f"{fname}.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(run, "call", fake_dcm2niix)
