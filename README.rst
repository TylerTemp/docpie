.. docpie
.. README.rst

docpie
======

`An easy and Pythonic way to create your POSIX command line`

View on: `HomePage <http://docpie.comes.today>`__ /
`GitHub <https://github.com/TylerTemp/docpie/>`__ /
`PyPi <https://pypi.python.org/pypi/docpie>`__

(中文说明参见 `README.zh.rst <https://github.com/TylerTemp/docpie/blob/master/README.zh.rst>`__)

.. contents::

ChangeLog
---------

version 0.2.1:

-   [fix] changing ``stdopt`` / ``attachopt`` / ``attachvalue``
    in ``set_config`` will re-initialize the instance. You should
    init a new ``Docpie`` instead of changing them.
-   [fix] argument using angle bracket can contain space and pipe.
    ``<a |b>`` is a correct argument.

`full changelog <https://github.com/TylerTemp/docpie/blob/master/CHANGELOG.md>`__


Introduction
------------

Isn't it brilliant how
`python-docopt <https://github.com/docopt/docopt>`__ parses the
``__doc__`` and converts command line into a python dict? ``docpie``
does the similar work, but...

**docpie can do more!**

If you have never used ``docpie`` or ``docopt``, try this. It can parse
your command line according to the ``__doc__`` string:

.. code:: python

    # example.py
    """Naval Fate.

    Usage:
      naval_fate.py ship new <name>...
      naval_fate.py ship <name> move <x> <y> [--speed=<km/h>]
      naval_fate.py ship shoot <x> <y>
      naval_fate.py mine (set|remove) <x> <y> [--moored | --drifting]
      naval_fate.py (-h | --help)
      naval_fate.py --version

    Options:
      -h --help     Show this screen.
      --version     Show version.
      --speed=<km/h>  Speed in knots. [default: 10]
      --moored      Moored (anchored) mine.
      --drifting    Drifting mine.

    """
    from docpie import docpie

    argument = docpie(__doc__, version='Naval Fate 2.0')
    print(argument)

`try it now >> <http://docpie.comes.today/try/?example=ship>`__

Then try ``$ python example.py ship Titanic move 1 2`` or
``$ python example.py --help``, see what you get.

**docpie can do...**

``docpie`` has some useful and handy features, e.g.

1. it allows you to specify the program name.

   .. code:: python

       '''Usage:
         myscript.py rocks
         $ python myscript.py rocks
         $ sudo python myscript.py rocks
       '''
       print(docpie(__doc__, name='myscript.py'))

   `try it now
   >> <http://docpie.comes.today/try/?example=myscript.py>`__

2. Different from ``docopt``, ``docpie`` will handle ``--``
   automatically by default, you do not need to write it in your
   "Usage:" anymore. (You can also turn off this feature)

   .. code:: python

       '''Usage:
        prog <hello>
       '''
       from docpie import docpie
       print(docpie(__doc__))

   `try it now >> <http://docpie.comes.today/try/?example=helloworld>`__

   Then ``$ python example.py test.py -- --world`` will give you
   ``{'--': True, '<hello>': '--world'}``

3. Some issues in ``docopt`` have been solved in ``dopie`` (try `#71
   >> <http://docpie.comes.today/try/?example=opt71>`__, `#282
   >> <http://docpie.comes.today/try/?example=opt282>`__, `#130
   >> <http://docpie.comes.today/try/?example=opt130>`__, `#275
   >> <http://docpie.comes.today/try/?example=opt275>`__, `#209
   >> <http://docpie.comes.today/try/?example=opt209>`__)

   **Note**: For this example, please see "`Known
   Issues <#known-issues>`__\ " for the details you need to pay
   attention to.

   .. code:: python

       '''
       Usage: mycopy.py <source_file>... <target_directory> <config_file>
       '''

       from docpie import docpie
       from docopt import docopt

       print('---- docopt ----')
       try:
          print(docopt(__doc__))
       except BaseException as e:
          print(e)

       print('---- docpie ----')
       try:
          print(docpie(__doc__))
       except BaseException as e:
          print(e)

   output:

   .. code:: bash

       $ python mycopy.py ./docpie/*.py ./docpie/test/*.py ~/my_project ~/config.cfg
       ---- docopt ----
       Usage: mycopy.py <source_file>... <target_directory> <config_file>
       ---- docpie ----
       {'--': False,
        '<config_file>': '/Users/tyler/config.cfg',
        '<source_file>': ['./docpie/setup.py', './docpie/test/*.py'],
        '<target_directory>': '/Users/tyler/my_project'}

   `try it now >> <http://docpie.comes.today/try/?example=mycopy.py>`__

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

Basic Usage
-----------

.. code:: python

    from docpie import docpie

Note that you can visit `HomePage <http://docpie.comes.today>`__ to have
a quick tutorial.

API
~~~

.. code:: python

    docpie(doc, argv=None, help=True, version=None,
           *,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, ...)

``docpie`` accepts 1 required argument, 3 optional arguments, and several
keyword arguments

-  ``doc`` is the description of your program which ``docpie`` can
   parse. It's usually the ``__doc__`` string of your python script, but
   it can also be any string in corrent format. The format is given in
   next section. Here is an example:

   .. code:: python

       """
       Usage: my_program.py [-hso FILE] [--quiet | --verbose] [INPUT ...]

       Options:
        -h --help    show this
        -s --sorted  sorted output
        -o FILE      specify output file [default: ./test.txt]
        --quiet      print less text
        --verbose    print more text
       """

   `try it now >> <http://docpie.comes.today/try/?example=docexample>`__

-  ``argv`` (sequence) is the command line your program accepted and it
   should be a list or tuple. By default ``docpie`` will use
   ``sys.argv`` if you omit this argument when it's called.
-  ``help`` (bool, default ``True``) tells ``docpie`` to handle ``-h`` &
   ``--help`` automatically. When it's set to ``True``, ``-h`` will
   print "Usage" and "Option" section, then exit; ``--help`` will print
   the whole ``doc``'s value and exit. set ``help=False`` if you want to
   handle it by yourself. See "`Advanced Usage <#advanced-usage>`__\ " -
   "`Auto Handler <#auto-handler>`__\ " if you want to customize the
   behavior.
-  ``version`` (any type, default ``None``) specifies the version of
   your program. When it's not ``None``, ``docpie`` will handle
   ``-v``/``--version``, print this value, and exit. See "`Advanced
   Usage <#advanced-usage>`__\ " - "`Auto Handler <#auto-handler>`__\ "
   if you want to customize the behavior.
-  ``auto2dashes`` (bool, default ``True``) When it's set ``True``,
   ``docpie`` will handle ``--`` (which means "end of command line
   flag", see
   `here <http://www.cyberciti.biz/faq/what-does-double-dash-mean-in-ssh-command/>`__
   )

   .. code:: python

       from docpie import docpie
       print(docpie('Usage: prog <file>'), ['prog', '--', '--test'])
       # {'--': True, '<file>': '--test'}

   `try it now >> <http://docpie.comes.today/try/?example=testfile>`__

-  ``name`` (str, default ``None``) is the "name" of your program. In
   each of your "usage" the "name" will be ignored. By default
   ``docpie`` will ignore the first element of your "usage"
-  ``optionsfirst``(bool, default ``False``). If set to ``True``, any
   elements after the first positional elements in ``argv`` will be
   interpreted as positional argument.

   .. code:: python

      '''
      Usage: sudo [-v] [<command>] [<options>...]
      '''

      from docpie import docpie
      import sys

      sys.argv = ['sudo', 'cp', '-v', 'a.txt', '/tmp']
      print(docpie(__doc__))
      # {'--': False,
      #  '-v': False,
      #  '<command>': 'cp',
      #  '<options>': ['-v', 'a.txt', '/tmp']}

      sys.argv = ['sudo', '-v', 'cp', '-v', 'a.txt', '/tmp']
      print(docpie(__doc__))
      # {'--': False,
      #  '-v': False,
      #  '<command>': 'cp',
      #  '<options>': ['-v', 'a.txt', '/tmp']}

   It's useful when you need to dispatch your program with others.
   See `example-get <https://github.com/TylerTemp/docpie/tree/master/docpie/example/git>`__

-  ``...`` other arguments please see "`Advanced Usage <#advanced-usage>`__"
   - "API"

the return value is a dictionary. Note if a flag has alias(e.g, ``-h`` &
``--help`` has the same meaning, you can specify in "Options"), all the
alias will also be in the result.

Format
~~~~~~

``docpie`` is indent sensitive.

Usage Format
^^^^^^^^^^^^

"Usage" starts with ``Usage:``\(case-insensitive). Use a *visibly*
empty line to separate with other parts.

.. code:: python

    """
    Usage: program.py

    This line is not part of usage.
    """

You can write more than one usage patterns

.. code:: python

    """
    Usage:
      program.py <from> <to>...
      program.py -s <source> <to>...
    """

`try it now >> <http://docpie.comes.today/try/?example=from_to>`__

When one usage pattern goes too long you can separate into several
lines, but the following lines need to indent more:

.. code:: python

    """
    Usage:
        prog [--long-option-1] [--long-option-2]
             [--long-option-3] [--long-option-4]  # Good
        prog [--long-option-1] [--long-option-2]
          [--long-option-3] [--long-option-4]     # Works but not so good
        prog [--long-option-1] [--long-option-2]
        [--long-option-3] [--long-option-4]       # Not work. Need to indent more.

    """

Each pattern can consist of the following elements:

-  **<arguments>**, **ARGUMENTS**. Arguments are specified as either
   upper-case words, e.g. ``my_program.py CONTENT-PATH`` or words
   surrounded by angular brackets: ``my_program.py <content-path>``.
-  **--options**. Short option starts with a dash(\ ``-``), followed by
   a character(\ ``a-z``, ``A-Z`` and ``0-9``), e.g. ``-f``. Long
   options starts with two dashes (``--``), followed by several
   characters(\ ``a-z``, ``A-Z``, ``0-9`` and ``-``), e.g. ``--flag``.
   You can "stack" several of
   short option, e.g. ``-oiv`` can mean ``-o -i -v``.

   The option can have argument. e.g. ``--input=FILE``, ``-i FILE``,
   ``-i<file>``. But it's important that you specify its argument in
   "Options"
-  **commands** are words that do *not* follow the described above. Note
   that ``-`` and ``--`` are also command.

Use the following constructs to specify patterns:

-  **[ ]** (brackets) **optional** elements. It does not matter if the
   elements are in the same pair of brackets or not. e.g.
   ``program.py [-abc]`` equals to ``program.py [-a] [-b] [-c]``
-  **( )** (parens) **required** elements. The elements inside must appear.
   All elements that are *not* put in **[ ]** are also required, e.g.:
   ``my_program.py --path=<path> <file>...`` is the same as
   ``my_program.py (--path=<path> <file>...)``.
-  **\|** (pipe) **mutually exclusive** elements. Use **( )** or **[ ]**
   to group them, e.g ``program.py (--left | --right)``. Note for
   ``program.py (<a> | <b> | <c>)``, because there is no difference
   between arguments, this will be parsed as ``program.py (<a>)`` and
   ``<b>``, ``<c>`` will be the alias of ``<a>``

   .. code:: python

       from docpie import docpie
       print(docpie('Usage: prog (<a> | <b>)', 'prog py'.split()))
       # {'--': False, '<a>': 'py', '<b>': 'py'}

   `try it now
   >> <http://docpie.comes.today/try/?example=either_args>`__

-  **...** (ellipsis) **repeatable** elements. To specify that arbitrary
   number of repeating elements could be accepted, use ellipsis
   (``...``), e.g. ``my_program.py FILE ...`` means one or more
   ``FILE``-s are accepted. If you want to accept zero or more elements,
   use brackets, e.g.: ``my_program.py [FILE ...]``. Ellipsis works as a
   unary operator on the expression to the left.
-  **[options]** (case sensitive) shortcut for any options. You can use
   it if you want to specify that the usage pattern could be provided
   with any options defined below in the option-descriptions and do not
   want to enumerate them all in usage-pattern.

   Note that you can wirte ``program.py [options]...``, but you can't
   break the format like ``program.py [options...]`` (in this case,
   ``options`` is a command)

you can several short options into one. ``-abc`` can mean ``-a -b -c``.

.. code:: python

   from docpie import docpie
   print(docpie('''Usage: prog -abc''', ['prog', '-a', '-bc']))
   # {'--': False, '-a': True, '-b': True, '-c': True}

`try it now >> <http://docpie.comes.today/try/?example=attachopt>`__

You can also write short option and its value together

.. code:: python

  '''
  Usage:
    prog [options]

  Options:
    -a <value>  -a expects one value
  '''
  from docpie import docpie
  print(docpie(__doc__, ['prog', '-abc']))
  # {'--': False, '-a': 'bc'}

`try it now
>> <http://docpie.comes.today/try/?example=attachvalue>`__

If your pattern allows to match argument-less option (a flag) several
times:

::

    Usage: my_program.py [-v | -vv | -vvv]

`try it now
>> <http://docpie.comes.today/try/?example=exclusive_good>`__

then number of occurrences of the option will be counted. I.e.
``args['-v']`` will be ``2`` if program was invoked as
``my_program -vv``. Same works for commands.

If your usage patterns allows to match same-named option with argument
or positional argument several times, the matched arguments will be
collected into a list:

::

    Usage: program.py <file> <file> --path=<path>...


`try it now >> <http://docpie.comes.today/try/?example=same_name>`__

(It's strongly suggested to specify it in "Options")

Then ``program.py file1 file2 --path ./here ./there`` will give you
``{'<file>': ['file1', 'file2'], '--path': ['./here', './there']}``

Also note that the ``...`` only has effect to ``<path>``. You can also
write in this way:

::

    Usage: program.py <file> <file> (--path=<path>)...

`try it now
>> <http://docpie.comes.today/try/?example=same_name_repeat_option>`__

Then it can match
``program.py file1 file2 --path=./here --path=./there`` with the same
result.

Options Format
^^^^^^^^^^^^^^

**Option descriptions** consist of a list of options that you put below
your usage patterns.

It is necessary to list option descriptions in order to specify:

-  synonymous short and long options,
-  if an option has an argument,
-  if option's argument has a default value.

"Options" starts with ``Options:`` (case-insensitive). descriptions can
followed it directly or on the next line. If you have rest content,
separate with an empty line.

e.g.

.. code:: python

    """
    Usage: prog [options]

    Options: -h"""

or

.. code:: python

    """
    Usage: prog [options]

    Options:
      -h, --help

    Not part of Options.
    """

You can write several "options" sections. It's the same to write it
together

::

    Global Options:
      -h, --help           print this message
      -v, --verbose        give more infomation
    Comment Options:
      -m, --message=<msg>  add message for comment

The rules in "Option" section are as follows:

-  To specify that option has an argument, put a word describing that
   argument after space (or equals "``=``\ " sign) as shown below.
   Follow either or UPPER-CASE convention for options' arguments. You
   can use comma if you want to separate options. In the example below,
   both lines are valid, however you are recommended to stick to a
   single style.

   ::

       -o FILE --output=FILE       # without comma, with "=" sign
       -i <file>, --input <file>   # with comma, without "=" sing

   You can also give several synonymous (only suggested in the following
   situation)

   ::

       -?, -h, --help

-  the description of the option can be written in two ways:

   1) separate option and description with 2+ empty spaces.
   2) start at the next line but indent 2+ empty spaces more.

   ::

       -?, -h, --help  print help message. use
                       -h/-? for a short help and
                       --help for a long help. # Good. 2+ empty spaces
       -a, --all
           A long long long long long long long
           long long long long long description of
           -a & --all    # Good. New line & indent 2 more spaces

   `try it now
   >> <http://docpie.comes.today/try/?example=option_format>`__

-  Use ``[default: <your-default-value>]`` at the end of the description
   if you need to provide a default value for an option. Note ``docpie``
   has a very strict format of default: it must start with
   ``[default:``, a space, followed by your
   default value, then ``]`` and no more, even a following dot is not
   acceptale.

   ::

       --coefficient=K  The K coefficient [default: 2.95]  # '2.95'
       --output=FILE    Output file [default: ]            # empty string
       --directory=DIR  Some directory [default:  ]        # a space
       --input=FILE     Input file[default: sys.stdout].   # not work because of the dot

   `try it now
   >> <http://docpie.comes.today/try/?example=example_default>`__

-  If the option is not repeatable, the value inside ``[default: ...]``
   will be interpreted as string. If it *is* repeatable, it will be
   splited into a list on whitespace:

   ::

       Usage: my_program.py [--repeatable=<arg> --repeatable=<arg>]
                            [--another-repeatable=<arg>]...
                            [--not-repeatable=<arg>]

       Options:
         --repeatable=<arg>          # will be ['./here', './there']
                                     [default: ./here ./there]
         --another-repeatable=<arg>  # will be ['./here']
                                     [default: ./here]
         --not-repeatable=<arg>      # will be './here ./there',
                                     # because it is not repeatable
                                     [default: ./here ./there]

   `try it now
   >> <http://docpie.comes.today/try/?example=repeat_default>`__

Though it's not POSIX standard, the following option argument format is
accepted in ``docpie``, which is not allowed in ``docopt``:

.. code:: python

    """
    Usage: prog [options]

    Options:
    -a..., --all ...               -a is countable
    -b<sth>..., --both=<sth>...  inf argument
    -c <a> [<b>]                   optional & required args
    -d [<arg>]                     optional arg
    """

    from docpie import docpie
    print(docpie(__doc__, 'prog -aa -a -b go go go -c sth else'.split()))
    # {'-a': 3, '--all': 3, '-b': ['go', 'go', 'go'], '--': False,
    #  '--both': ['go', 'go', 'go'], '-c': ['sth', 'else'], '-d': None}

`try it now
>> <http://docpie.comes.today/try/?example=non_posix_option>`__

Advanced Usage
--------------

Normally the ``docpie`` and the basic arguments are all your need,
But you can do more tricks with ``Docpie`` class.

.. code:: python

    from docpie import Docpie

Basic
~~~~~

when call

.. code:: python

    from docpie import docpie
    print(docpie(__doc__))

it's equal to:

.. code:: python

    from docpie import Docpie
    pie = Docpie(__doc__)
    pie.docpie()
    print(pie)

API
~~~

.. code::python

   docpie(doc, argv=None, help=True, version=None,
          stdopt=True, attachopt=True, attachvalue=True,
          auto2dashes=True, name=None, case_sensitive=False,
          optionsfirst=False, appearedonly=False, extra={})

The left arguments that have not introduced are as follow:

-  ``stdopt`` (bool, default ``True``, **experimental**) when set ``True``
   (default), long option should only starts with ``--``, e.g. ``--help``, and
   short option should be ``-`` followed by a letter. This is suggested to make
   it ``True``. When set to ``False``, ``-flag`` is also a long flag.
   (Some old program like ``find`` use this format)
-  ``attachopt`` (bool, default ``True``, **experimental**) allow you to
   write/pass several short option into one, e.g. ``-abc`` can mean ``-a -b -c``.
   This only works when ``stdopt=True``.
-  ``attachvalue`` (bool, default ``True``, **experimental**) allow you to
   write short option and its value together, e.g. ``-abc`` can mean ``-a bc``.
   This only works when ``stdopt=True``.
-  ``case_sensitive`` (bool, default ``False``) specifies if it need
   case sensitive when matching "Usage:" and "Options:"
-  ``appearedonly`` (bool, default ``False`` ). When set to ``True``,
   ``docpie`` will not add options that never appeared in ``argv``.
   Consider the following situation:

   ::

      Usage: prog [options]

      Options:
         -s, --sth=[<value>]    Just an example. Not POSIX standard

   In result ``{'-s': None, '--sth': None}``, it's not clear wether user
   inputs a value for ``--sth``. So if ``appearedonly=True``, then
   ``'--sth'`` will not appear in result if user never use this
   options. Note: 1. It's not POSIX standard. 2. It only affect
   options.
-  ``extra`` see the section below

.. code:: python

    Docpie(doc=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, appearedonly=False, extra={})

``Docpie`` accepts all arguments of ``docpie`` function except
the ``argv``.

.. code:: python

    pie = Docpie(__doc__)
    pie.docpie(argv=None)

``Docpie.docpie`` accepts ``argv`` which is the same ``argv`` in
``docpie``

Change Configuration
~~~~~~~~~~~~~~~~~~~~

.. code:: python

    Docpie.set_config(self, **config)

``set_config`` allows you to change the argument after you initialized
``Docpie``. ``**config`` is a dict, and the keys can only be what
``__init__`` accepts except ``doc``

Note changing ``stdopt`` / ``attachopt`` / ``attachvalue`` will re-initialize
the instance. You may init a new ``Docpie`` instance.

.. code:: python

    pie = Docpie(__doc__)
    pie.set_config(help=False)  # now Docpie will not handle `-h`/`--help`
    pie.docpie()

Auto handler
~~~~~~~~~~~~

Docpie has an attribute called ``extra``. ``extra`` is a dict, the key
is an option (str), and the value is a function. the function accepts
two arguments, the first will be the ``Docpie`` instance, the second is
the the same of the key.

it may lookes like:

.. code:: python

    {'-h': <function docpie.Docpie.help_handler>,
     '--help': <function docpie.Docpie.help_handler>,
     '-v': <function docpie.Docpie.version_handler>,
     '--version': <function docpie.Docpie.version_handler>,
    }

When ``version`` is not ``None``, Docpie will do the following things
(``pie`` is the instance of ``Docpie``):

1. set ``pie.version`` to this value
2. check if "--version" is defined in "Options"
3. if it is, set "--version" and its synonymous options as
   ``pie.extra``'s key, the ``pie.version_handler`` as value
4. if not, check if "-v" is defined in "Options", and do similar work as
   step ``3``
5. if neither "-v" nor "--version" is defined in "Options", then just
   add "-v" & "--version" as keys of ``pie.extra``, the values are
   ``Docpie.version_handler``
6. when call ``pie.docpie``, ``Docpie`` checks if the keys in
   ``pie.extra`` appears in ``argv``.
7. if it finds the key, to say ``-v`` for example, ``Docpie`` will call
   ``pie.extra["-v"](pie, "-v")``.
8. By default, ``Docpie.version_handler(docpie, flag)`` will print
   ``pie.version``, and exit the program.

for ``help=True``, ``Docpie`` will check "--help" and "-h", then set
value as ``Docpie.help_handler``.

There are two ways to customize it:

extra argument
^^^^^^^^^^^^^^

You can costomize this by passing ``extra`` argument, e.g.

.. code:: python

    """
    Example for Docpie!

    Usage: example.py [options]

    Options:
      -v, --obvious    print more infomation  # note the `-v` is here
      --version        print version
      -h, -?, --help   print this infomation

    Hidden Options:
      --moo            the Easter Eggs!

    Have fun, my friend.
    """
    from docpie import Docpie
    import sys


    def moo_handler(pie, flag):
        print("Alright you got me. I'm an Easter Egg.\n"
              "You may use this program like this:\n")
        print(pie.usage_text)
        print("")    # compatible python2 & python3
        print(pie.option_sections[''])
        sys.exit()    # Don't forget to exit

    pie = Docpie(__doc__, version='0.0.1')
    pie.set_config(
      extra={
        '--moo': moo_handler,  # set moo handler
      }
    )

    pie.docpie()
    print(pie)

now try the following command:

.. code:: bash

    example.py -v
    example.py --version
    example.py -h
    example.py -?
    example.py --help
    example.py --moo

What is ``option_sections``? See "Docpie Attribute" section below

set_auto_handler
^^^^^^^^^^^^^^^^

.. code:: python

    Docpie.set_auto_handler(self, flag, handler)

When set ``extra``, the synonymous options you defined will not be
checked by ``Docpie``. But ``set_auto_handler`` can do the check and
make all synonymous options have the same behavior. e.g.

.. code:: python

    """
    Usage: [options]

    Options: --moo, -m     the Easter Eggs!
    """

    from docpie import Docpie
    import sys

    def moo_handler(pie, flag):
        print("I'm an Easter Egg!")
        sys.exit()

    pie = Docpie(__doc__)
    pie.set_auto_handler('-m', moo_handler)
    pie.docpie()
    print(pie)

Then ``Docpie`` will handle both ``-m`` & ``--moo``.


Docpie Attribute
~~~~~~~~~~~~~~~~

(``pie`` is the instance of ``Docpie``)

to customize your ``extra``, the following attribute of ``Docpie`` may
help:

-  ``pie.version`` is the version you set. (default ``None``)
-  ``pie.usage_text`` is the usage section.
-  ``pie.option_sections`` is a ``dict`` containing all ``Options``
   sections you defined. The key depends on the string ahead of "Options:"

   ::

      usage: example.py <command> [options]

      # the key will be an empty string
      options:
         -h, --help        print this message

      # the key will be 'help'
      help options:
         -o, --out=<file>  output file

      # the key will be 'advanced control'
      advanced control options:
         -u, --up          move upward
         -d, --down        move downward


Serialization
~~~~~~~~~~~~~

(``pie`` is the instance of ``Docpie``)

``pie.convert_2_dict()`` can convert ``Docpie`` instance into a
dict so you can JSONlizing it. Use ``Docpie.convert_2_docpie(dic)``
to convert back to ``Docpie`` instance.

**Note:** if you change ``extra`` by passing ``extra`` argument or calling
``set_auto_handler``, the infomation will be lost because JSON can not save
function object. You need to call ``set_config(extra={...})`` or
``set_auto_handler`` after ``convert_2_docpie``.

Here is a full example of serialization and unserialization together
with `pickle <https://docs.python.org/3/library/pickle.html>`__

In developing:

.. code:: python

    """
    This is my cool script!

    Usage: script.py [options] (--here|--there)

    Options:
      --here
      --there
      -h, --help
      -v, --version

    Have fun then.
    """

    import json
    try:
        import cPickle as pickle
    except ImportError:    # py3 maybe
        import pickle
    from docpie import Docpie


    pie = Docpie(__doc__)

    with open('myscript.docpie.pickle', 'wb') as pkf:
        pickle.dump(pie, pkf)

    # omit `encoding` if you're using python2
    with open('myscript.docpie.json', 'w', encoding='utf-8') as jsf:
        json.dump(pie.convert_2_dict(), jsf)

In release:

.. code:: python

    """
    This is my cool script!

    Usage: script.py [options] (--here|--there)

    Options:
      --here
      --there
      -h, --help
      -v, --version

    Have fun then.
    """

    import os
    import json
    try:
        import cPickle as pickle
    except ImportError:    # py3 maybe
        import pickle
    from docpie import Docpie

    pie = None

    if os.path.exists('myscript.docpie.pickle'):
        with open('myscript.docpie.pickle', 'rb') as pkf:
            try:
                pie = pickle.load(pkf)
            except BaseException:
                pass

    if pie is None and os.path.exists('myscript.docpie.json'):
        # omit `encoding` if you're using python2
        with open('myscript.docpie.json', 'r', encoding='utf-8') as jsf:
            try:
                pie = Docpie.convert_2_docpie(json.load(jsf))
            except BaseException:
                pass
            else:
                # set extra if you have changed `extra` before
                pie.set_config(extra={})

    if pie is None:
        pie = Docpie(__doc__)

    print(pie.docpie())

preview
~~~~~~~

after you get your ``pie=Docpie(__doc__)`` instance, you can call
``pie.preview()`` to have a quick view of how ``Docpie`` understands
your ``doc``

*Note* because the ``option``-s position does not effect the result of
matching, ``Docpie`` will push all ``option``-s to the front, which will
cause the preview is not the same as what you write.

Difference
----------

``docpie`` is not ``docopt``.

1. ``docpie`` uses ``Options:`` to find the current "Option" section,
   however ``docopt`` treats any line in ``doc`` that starts with ``-``
   (not counting spaces) as "Options"

2. ``docpie`` will add ``--`` to result when ``auto2dashes=True``.
   ``docpie`` will add all synonymous to result.

Known Issues
------------

Currently, ``docpie`` can support arguments after repeated argument, but
this feature has a very strict limit.

::

    Usage: cp.py <source_file>... <target_directory> [-f] [-r]

1. the repeated argument should be and only be one ``ARGUMENT``, which
   means:

   -  YES: ``(<arg1>)... <arg2> <arg3>``
   -  YES: ``[<arg1>]... <arg2>``
   -  NO: ``(<arg1> <arg2>)... <arg3>``
   -  NO: ``-a... -a``
   -  NO: ``cmd... cmd``

2. the elements after repeatable argument
   can only be ``ARGUMENT``-s (even can not be grouped by ``()`` or
   ``[]``)

   -  ``<arg1>... <arg2> <arg2> command``:  won't match
      ``val1 val2 val3 command``
   -  ``<arg1>... (<arg2>)`` won't work,

Development
-----------

execute ``/test.py`` to run the test

the logger name of ``docpie`` is ``"docpie"``

``docpie`` contains two developing tools: ``bashlog`` and ``tracemore``.
You can use them in this way:

.. code:: python

    from docpie import docpie, bashlog
    from docpie.tracemore import get_exc_plus

    logger = bashlog.stdoutlogger('docpie')  # You may init your logger in your way

    try:
        docpie(doc)
    except BaseException:
        logger.error(get_exc_plus())

the code in ``bashlog.py`` is taken from
`tornado <https://github.com/tornadoweb/tornado>`__, and
``tracemore.py`` is from `python
Cookbook <http://www.amazon.com/Python-Cookbook-Third-David-Beazley/dp/1449340377/ref=sr_1_1?ie=UTF8&qid=1440593849&sr=8-1&keywords=python+cookbook>`__

License
-------

``docpie`` is released under
`MIT-License <https://github.com/TylerTemp/docpie/blob/master/LICENSE>`__
