.. docpie
.. README.rst

docpie
======

`An easy and Pythonic way to create your POSIX command line`

View on: `GitHub <https://github.com/TylerTemp/docpie/>`__ /
`PyPi <https://pypi.org/project/docpie/>`__

.. image:: https://travis-ci.org/TylerTemp/docpie.svg?branch=master
    :target: https://travis-ci.org/TylerTemp/docpie

.. contents::

ChangeLog
---------

version 0.4.4:

change auto balance function, fix the issue that won't work for this case

.. code-block:: python

    """
    Usage:
        cp [options] <source>... <target>

    Options:
        -R
    """

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
     cp.py [options] <source_file>... <target_directory>

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

   $ python cp.py a.txt b.txt c.txt /tmp
   {'--': False,
    '--help': False,
    '--verbose': False,
    '--version': False,
    '-?': False,
    '-h': False,
    '-v': False,
    '<source_file>': ['a.txt', 'b.txt', 'c.txt'],
    '<target_directory>': '/tmp',
    '<target_file>': None}

Write a ``__doc__``, pass it to a function, DONE! Isn't it simple?

`try it \>\> <http://docpie.comes.today/try?argvnofilestr=a.txt%20b.txt%20c.txt%20%2Ftmp&attachopt=on&attachvalue=on&auto2dashes=on&doc=My%20copy%20script%5Cn%5CnUsage%3A%5Cn%20%20cp.py%20%5Boptions%5D%20%3Csource_file%3E%20%3Ctarget_file%3E%5Cn%20%20cp.py%20%5Boptions%5D%20%3Csource_file%3E...%20%3Ctarget_directory%3E%5Cn%5CnOptions%3A%5Cn%20%20-h%20-%3F%20--help%20%20%20%20print%20this%20screen%5Cn%20%20--version%20%20%20%20%20%20%20print%20the%20version%20of%20this%20script%5Cn%20%20-v%20--verbose%20%20%20%20print%20more%20information%20while%20%20running&help=on&replace=on&stdopt=on>`__

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
