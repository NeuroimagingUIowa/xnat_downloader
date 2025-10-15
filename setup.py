from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).resolve().parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8")


setup(
    name="xnat_downloader",
    version="0.3.0",
    description="Downloads XNAT DICOMs and stores the results in a BIDS-like structure.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/NeuroimagingUIowa/xnat_downloader",
    author="James Kent",
    author_email="james-kent@uiowa.edu",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pyxnat>=1.6.3",
        "xmltodict>=0.13.0",
        "cryptography>=41.0.0",
        "pyopenssl>=23.2.0",
    ],
    extras_require={
        "test": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "xnat_downloader=xnat_downloader.cli.run:main",
        ]
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
)
