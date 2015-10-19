.. docpie
.. README.rst

docpie
======

`An easy and Pythonic way to create your POSIX command line`

View on: `HomePage <http://docpie.comes.today>`__ /
`GitHub <https://github.com/TylerTemp/docpie/>`__ /
`PyPi <https://pypi.python.org/pypi/docpie>`__

.. contents::

ChangeLog
---------

version 0.2.2:

-   [fix] a bug in test that some tests will not report even they
    fail
-   [fix] ``help`` & ``version`` won't work because of the previous refactor, sorry

`full changelog <https://github.com/TylerTemp/docpie/blob/master/CHANGELOG.md>`__


Summary
-------

How do you define your command line interface?
Write a parse by yourself or spend hours learning ``optparse`` / ``argparse`` ,
and modify both code side and document every time you update the interface?


Life is short, man! You can simply do it this way:

.. code:: python

   """
   My copy script

   Usage:
     cp.py [options] <source_file> <target_file>
     cp.py [options] <source_file>... <target_directory> <log_file>

   Options:
     -h -? --help    print this screen
     --version       print the version of this script
     -v --verbose    print more information while  running
   """

   from docpie import docpie
   args = docpie(__doc__)
   print(args)

Now run it

.. code:: bash
   $ python cp.py a.txt b.txt c.txt /tmp cp.log
   {'--': False,
    '--help': False,
    '--verbose': False,
    '--version': False,
    '-?': False,
    '-h': False,
    '-v': False,
    '<log_file>': 'cp.log',
    '<source_file>': ['a.txt', 'b.txt', 'c.txt'],
    '<target_directory>': '/tmp',
    '<target_file>': None}

Write a ``__doc__``, pass it to a function, DONE! Isn't it simple?

[try it \>\>](http://docpie.comes.today/try?example=ship)

Installation
------------

Install release version:

.. code:: python

    pip install docpie

Install nightly/dev version:

.. code:: bash

    pip install git+git://github.com/TylerTemp/docpie.git

``docpie`` has been tested with Python:

2.6, 2.7

3.2, 3.3, 3.4, 3.5

pypy-2.0, pypy-2.6, pypy3-2.4

Get Start!
----------

Interested? Visit `Document <http://docpie.comes.today/document/quick-start/>`__
and get start!

Or you can `try it in your browser <docpie.comes.today/try/>`__:

Why docpie?
-----------

See `here <http://docpie.comes.today/document/why-docpie/>`__ for more reasons.

Reference
---------

the code in ``bashlog.py`` is taken from
`tornado <https://github.com/tornadoweb/tornado>`__, and
``tracemore.py`` is from `python
Cookbook <http://www.amazon.com/Python-Cookbook-Third-David-Beazley/dp/1449340377/ref=sr_1_1?ie=UTF8&qid=1440593849&sr=8-1&keywords=python+cookbook>`__

License
-------

``docpie`` is released under
`MIT-License <https://github.com/TylerTemp/docpie/blob/master/LICENSE>`__
