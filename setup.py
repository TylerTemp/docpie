# from distutils.core import setup
from setuptools import setup
import os

from docpie import __version__

setup(
    name="docpie",
    packages=["docpie"],
    package_data={
        '': [
            'README.rst',
            'LICENSE',
            'CHANGELOG.md'
        ],
        'docpie': [
            'example/*.py',
            'example/git/*.py',
            'utest/*.py'
      ],
    },
    version=__version__,
    author="TylerTemp",
    author_email="tylertempdev@gmail.com",
    url="http://docpie.comes.today/",
    download_url="https://github.com/TylerTemp/docpie/tarball/0.2.0/",
    license='MIT',
    description=("An easy and Pythonic way to create "
                 "your POSIX command line interface"),
    keywords='option arguments parsing optparse argparse getopt',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    platforms='any',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        ],
)
