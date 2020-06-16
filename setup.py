from setuptools import setup, find_packages

setup(name='xnat_downloader',
      version='0.2.8',
      description='(uiowa) Downloads xnat dicoms in a BIDS(ish) way',
      url='https://github.com/HBClab/xnat_downloader',
      author='James Kent',
      author_email='james-kent@uiowa.edu',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        'pyxnat',
        'xmltodict',
        'cryptography',
        'pyOpenSSL',
      ],
      extras_require={
        'test': ['pytest'],
      },
      entry_points={'console_scripts': [
            'xnat_downloader=xnat_downloader.cli.run:main'
        ]},
      zip_safe=False)
