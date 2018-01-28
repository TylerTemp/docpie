.. docpie
.. README.rst

docpie
======

`An easy and Pythonic way to create your POSIX command line`

View on: `GitHub <https://github.com/TylerTemp/docpie/>`__ /
`PyPi <https://pypi.python.org/pypi/docpie>`__

.. image:: https://travis-ci.org/TylerTemp/docpie.svg?branch=master
    :target: https://travis-ci.org/TylerTemp/docpie

.. contents::

ChangeLog
---------

version 0.4.0:

-   [fix] `#10 <https://github.com/TylerTemp/docpie/issues/10>`__,
    `#11 <https://github.com/TylerTemp/docpie/issues/11>`__ short help(`-h`) print
    full doc
-   [new] **breaking change**. `PEP-257 <https://www.python.org/dev/peps/pep-0257/>`__
    help message supported. add ``helpstyle`` for people how need to print
    raw docsting as help message (the old way)

    that means, when there is extra returning line, extra indent, they will be
    trimly. This feature makes ``docpie`` work as most python doc tool.

    This is very useful when your doc needs to be written as:

    .. code:: python

        class Test(object):

            def some_fun(self):
                """
                Usage: prog hello
                """

    and also in this way:

    .. code:: python

        docpie.docpie("\n \n Usage: prog [-h]\n\n\n", ["prog", "-h"])
        # will give `Usage: prog [-h]\n` instead of `\n \n Usage: prog [-h]\n\n\n\n`

    supported value for ``helpstyle``: ``"python"`` (default), ``"dedent"``, ``"raw"``

`full changelog & TODOs <https://github.com/TylerTemp/docpie/blob/master/CHANGELOG.md>`__


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

`try it \>\> <http://docpie.comes.today/try?example=ship>`__

Installation
------------

Install release version:

.. code:: python

    pip install docpie

Install nightly/dev version:

.. code:: bash

    pip install git+https://github.com/TylerTemp/docpie.git@dev

``docpie`` has been tested with Python:

-   2.6, 2.7, pypy-2.0, pypy-2.6
-   3.2, 3.3, 3.4, 3.5, pypy3-2.4

You can run test suit by ``python setup.py test``

Get Start!
----------

Interested? Visit `Wiki <https://github.com/TylerTemp/docpie/wiki>`__
and get start!

Or you can `try it in your browser <http://docpie.comes.today/try/>`__

Why docpie?
-----------

``docpie`` can greatly reduce the work you need to be done for
command-line interface. What you see is what you get.
Every time you only need to update your document, and keep the
code unchanged.

See `here <https://github.com/TylerTemp/docpie/wiki/Why-docpie>`__ for more reasons.

Reference
---------

the code in ``bashlog.py`` is taken from
`tornado <https://github.com/tornadoweb/tornado>`__, and
``tracemore.py`` is from `python
Cookbook <http://www.amazon.com/Python-Cookbook-Third-David-Beazley/dp/1449340377/ref=sr_1_1?ie=UTF8&qid=1440593849&sr=8-1&keywords=python+cookbook>`__

Many examples & tests are from ``docopt``.

License
-------

``docpie`` is released under
`MIT-License <https://github.com/TylerTemp/docpie/blob/master/LICENSE>`__

Donate
------

If you like this project, you can buy me a beer so I can make it better!

.. image:: https://dn-tyler.qbox.me/alipay.ico
    :target: https://dn-tyler.qbox.me/myalipay.png

.. image:: https://button.flattr.com/flattr-badge-large.png
    :target: https://flattr.com/submit/auto?user_id=TylerTemp&url=http%3A%2F%2Fdocpie.comes.today
