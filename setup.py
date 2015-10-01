from distutils.core import setup
import os

from docpie import __version__

setup(
    name="docpie",
    packages=["docpie", "docpie.test"],
    version=__version__,
    author="TylerTemp",
    author_email="tylertempdev@gmail.com",
    url="http://docpie.comes.today/",
    download_url="https://github.com/TylerTemp/docpie/tarball/0.1.1/",
    license='MIT',
    description=("An easy and Pythonic way to create "
                 "your POSIX command line interface"),
    keywords='option arguments parsing optparse argparse getopt',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    # package_data={'': ['../LICENSE', 'test/*']},
    package_data={'': ['test/*', 'README.*', '*.md']},
    # data_files=[('docpie', ['./LICENSE'])],
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
