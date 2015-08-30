docpie
======

Please read this
`issue#1 <https://github.com/TylerTemp/docpie/issues/1>`__ before using.
I'm still woking on it.

Intro
-----

Isn't it brilliant how
`python-docopt <https://github.com/docopt/docopt>`__ parses the
``__doc__`` and converts command line into a python dict? ``docpie``
does the similar work, but...

**``docpie`` can do more!**

If you have never used ``docpie`` or ``docopt``, try this. It can parse
your command line according to the ``__doc__`` string:

.. code:: python

    # example.py
    """Naval Fate.

    Usage:
      naval_fate.py ship new <name>...
      naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
      naval_fate.py ship shoot <x> <y>
      naval_fate.py mine (set|remove) <x> <y> [--moored | --drifting]
      naval_fate.py (-h | --help)
      naval_fate.py --version

    Options:
      -h --help     Show this screen.
      --version     Show version.
      --speed=<kn>  Speed in knots. [default: 10]
      --moored      Moored (anchored) mine.
      --drifting    Drifting mine.

    """
    from docpie import docpie

    argument = docpie(__doc__, version='Naval Fate 2.0')
    print(argument)

Then try ``$ python example.py ship Titanic move 1 2`` or
``$ python example.py --help``, see what you get.

**``docpie`` can do...**

``docpie`` has some useful and handy features, e.g.

1. it allow you to specify the program name.

   .. code:: python

       '''Usage:
         myscript.py rocks
         $ python myscript.py rocks
         $ sudo python myscript.py rocks
       '''
       print(docpie(__doc__, name='myscript.py'))

2. Different from ``docopt``, ``docpie`` will handle ``--``
   automatically by default, you do not need to write it in your
   "Usage:" anymore. (You can also trun off this feature)

   .. code:: python

       '''Usage:
        prog <hello>
       '''
       from docpie import docpie
       print(docpie(__doc__))

   Then ``$ python example.py test.py -- --world`` will give you
   ``{'--': True, '<hello>': '--world'}``

3. Some issues in ``docopt`` have been solved in ``dopie`` (e.g.
   `#71 <https://github.com/docopt/docopt/issues/71>`__,
   `#282 <https://github.com/docopt/docopt/issues/282>`__,
   `#130 <https://github.com/docopt/docopt/issues/130>`__,
   `#275 <https://github.com/docopt/docopt/issues/275>`__,
   `#209 <https://github.com/docopt/docopt/issues/209>`__)

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

Installation
------------

.. code:: python

    pip install docpie

or

.. code:: bash

    pip install git+git://github.com/TylerTemp/docpie.git

``docopt`` has been tested with Python:

2.6.6, 2.6.9, 2.7, 2.7.10,

3.2, 3.3.0, 3.3.6, 3.4.0, 3.4.3,

pypy-2.0, pypy-2.6.0, pypy3-2.4.0

Basic Usage
-----------

.. code:: python

    from docpie import docpie

.. code:: python

    docpie(doc, argv=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False, extra={})

Note that it's strongly suggested that you pass keyword arguments
instead of positional arguments.

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

-  ``argv`` (sequence) is the command line your program accepted and it
   should be a list or tuple. By default ``docpie`` will use
   ``sys.argv`` if you omit this argument when it's called.
-  ``help`` (bool, default ``True``) tells ``docpie`` to handle ``-h`` &
   ``--help`` automatically. When it's set to ``True``, ``-h`` will
   print "Usage" and "Option" section, then exit; ``--help`` will print
   the whole ``doc``'s value and exit. set ``help=False`` if you want to
   handle it by yourself. Use ``extra`` (see below) or see ``Docpie`` if
   you only want to change ``-h``/``--help`` behavior.
-  ``version`` (any type, default ``None``) specifies the version of
   your program. When it's not ``None``, ``docpie`` will handle
   ``-v``/``--version``, print this value, and exit. See "`Advanced
   Usage <#advanced-usage>`__\ " - "`Auto Handler <#auto-handler>`__\ "
   if you want to customize it.
-  ``stdopt`` (bool, default ``True``) when set ``True``\ (default),
   long flag should only starts with ``--``, e.g. ``--help``, and short
   flag should be ``-`` followed by a letter. This is suggested to make
   it ``True``. When set to ``False``, ``-flag`` is also a long flag. Be
   careful if you need to turn it off.
-  ``attachopt`` (bool, default ``True``) allow you to write/pass
   several short flag into one, e.g. ``-abc`` can mean ``-a -b -c``.
   This only works when ``stdopt=True``

   .. code:: python

       from docpie import docpie
       print(docpie('''Usage: prog -abc''', ['prog', '-a', '-bc']))
       # {'--': False, '-a': True, '-b': True, '-c': True}

-  ``attachvalue`` (bool, default ``True``) allow you to write short
   flag and its value together, e.g. ``-abc`` can mean ``-a bc``. This
   only works when ``stdopt=True``

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

-  ``auto2dashes`` (bool, default ``True``) When it's set ``True``,
   ``docpie`` will handle ``--`` (which means "end of command line
   flag", see
   `here <http://www.cyberciti.biz/faq/what-does-double-dash-mean-in-ssh-command/>`__
   )

   .. code:: python

       from docpie import docpie
       print(docpie('Usage: prog <file>'), ['prog', '--', '--test'])
       # {'--': True, '<file>': '--test'}

-  ``name`` (str, default ``None``) is the "name" of your program. In
   each of your "usage" the "name" will be ignored. By default
   ``docpie`` will ignore the first element of your "usage"
-  ``case_sensitive`` (bool, default ``False``) specifies if it need
   case sensitive when matching "Usage:" and "Options:"
-  ``extra`` see "`Advanced Usage <#advanced-usage>`__\ " - "`Auto
   Handler <#auto-handler>`__\ "

the return value is a dictionary. Note if a flag has alias(e.g, ``-h`` &
``--help`` has the same meaning, you can specify in "Options"), all the
alias will also be in the result.

Format
------

``docpie`` is indent sensitive.

Usage Format
~~~~~~~~~~~~

"Usage" starts with ``Usage:``\ (set ``case_sensitive`` to make it case
sensitive/insensitive), ends with a *visibly* empty line.

.. code:: python

    """
    Usage: program.py

    """

You can write more than one usage patterns

.. code:: python

    """
    Usage:
      program.py <from> <to>...
      program.py -s <source> <to>...

    """

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
   options starts with two dashes (``--``), followed by seveval
   characters(\ ``a-z``, ``A-Z``, ``0-9`` and ``-``), e.g. ``--flag``.
   When ``stdopt`` and ``attachopt`` are on, you can "stack" seveval of
   short option, e.g. ``-oiv`` can mean ``-o -i -v``.

   The option can have value. e.g. ``--input=FILE``, ``-i FILE``,
   ``-i<file>``. But it's important that you specify its argument in
   "Options"
-  **commands** are words that do *not* follow the described above. Note
   that ``-`` and ``--`` are also command.

Use the following constructs to specify patterns:

-  **[ ]** (brackets) **optional** elements. Note the elements in
   brackets should either be all omitted or provided. e.g.
   ``program.py [-ab]`` will only match ``-ab``, ``-a -b`` or \`
   \`(empty argument)
-  **( )** (parens) **required** elements. All elements that are *not*
   put in **[ ]** are also required, e.g.:
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

If your pattern allows to match argument-less option (a flag) several
times:

::

    Usage: my_program.py [-vvv | -vv | -v]

then number of occurrences of the option will be counted. I.e.
``args['-v']`` will be ``2`` if program was invoked as
``my_program -vv``. Same works for commands.

Note that the ``|`` acts like ``or`` in python, which means if one
elements group matched, the following groups will be skipped. usage like
``program.py [-v | -vv | -vvv]`` will not match ``program.py -vv``,
because the first ``-v`` matches first part of ``-vv``, and then nothing
left to match the rest argv, so it fails.

If your usage patterns allows to match same-named option with argument
or positional argument several times, the matched arguments will be
collected into a list:

::

    Usage: program.py <file> <file> --path=<path>...

    Options: --path=<path>...     the path you need

(It's strongly suggested to specify it in "Options")

Then ``program.py file1 file2 --path ./here ./there`` will give you
``{'<file>': ['file1', 'file2'], '--path': ['./here', './there']}``

Also note that the ``...`` only has effect to ``<path>``. You can also
write in this way:

::

    Usage: program.py <file> <file> (--path=<path>)...

    Options: --path=<path>     the path you need

Then it can match
``program.py file1 file2 --path=./here --path=./there`` with the same
result.

Options Format
~~~~~~~~~~~~~~

**Option descriptions** consist of a list of options that you put below
your usage patterns.

It is necessary to list option descriptions in order to specify:

-  synonymous short and long options,
-  if an option has an argument,
-  if option's argument has a default value.

"Options" starts with ``Options:`` (set ``case_sensitive`` to make it
case sensitive/insensitive). descriptions can followed it directly or on
the next line. If you have rest content, separate with an empty line.

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

-  Use ``[default: <your-default-value>]`` at the end of the description
   if you need to provide a default value for an option. Note ``docpie``
   has a very strict format of default: it must start with
   ``[default:``\ (note the empty space after ``:``), followed by your
   default value, then ``]`` and no more, even a following dot is not
   acceptale.

   ::

       --coefficient=K  The K coefficient [default: 2.95]  # '2.95'
       --output=FILE    Output file [default: ]            # empty string
       --directory=DIR  Some directory [default:  ]        # a space
       --input=FILE     Input file[default: sys.stdout].   # not work because of the dot

-  If the option is not repeatable, the value inside ``[default: ...]``
   will be interpreted as string. If it *is* repeatable, it will be
   splited into a list on whitespace:

   ::

       Usage: my_program.py [--repeatable=<arg> --repeatable=<arg>]
                            [--another-repeatable=<arg>]...
                            [--not-repeatable=<arg>]

       # will be ['./here', './there']
       --repeatable=<arg>          [default: ./here ./there]

       # will be ['./here']
       --another-repeatable=<arg>  [default: ./here]

       # will be './here ./there', because it is not repeatable
       --not-repeatable=<arg>      [default: ./here ./there]

Though it's not POSIX standard, the following option argument format is
accepted in ``docpie``, which is not allowed in ``docopt``:

.. code:: python

    """
    Usage: prog [options]

    Options:
    -a..., --all ...               -a is countable
    -b<sth>..., --boring=<sth>...  inf argument
    -c <a> [<b>]                   optional & required args
    -d [<arg>]                     optional arg
    """

    from docpie import docpie
    print(docpie(__doc__, 'prog -aa -a -b go go go -c sth else'.split()))
    # {'-a': 3, '--all': 3, '-b': ['go', 'go', 'go'], '--': False,
    #  '--boring': ['go', 'go', 'go'], '-c': ['sth', 'else'], '-d': None}

Advanced Usage
--------------

Normally the ``docpie`` is all you need, But you can do more tricks with
``Docpie``

.. code:: python

    from docpie import Docpie

Basic Usage
~~~~~~~~~~~

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

.. code:: python

    Docpie.__init__(self, doc=None, help=True, version=None,
                    stdopt=True, attachopt=True, attachvalue=True,
                    auto2dashes=True, name=None, case_sensitive=False, extra={})

``Docpie.__init__`` accepts all arguments of ``docpie`` function except
the ``argv``.

.. code:: python

    Docpie.docpie(self, argv=None)

``Docpie.docpie`` accepts ``argv`` which is the same ``argv`` in
``docpie``

Change Config
~~~~~~~~~~~~~

.. code:: python

    Docpie.set_config(self, **config)

``set_config`` allows you to change the argument after you initialized
``Docpie``. ``**config`` is a dict, and the keys can only be what
``__init__`` accepts except ``doc``

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

When ``version`` is not ``None``, Docpie will do the following things:

1. set ``Docpie.version`` to this value
2. check if "--version" is defined in "Options"
3. if it is, set "--version" and its synonymous flags as
   ``Docpie.extra``'s key, the ``Docpie.version_handler`` as value
4. if not, check if "-v" is defined in "Options", and do similar work as
   ``3``
5. if neither "-v" nor "--version" is defined in "Options", then just
   add "-v" & "--version" as keys of ``Docpie.extra``, the values are
   ``Docpie.version_handler``
6. when call ``Docpie.docpie``, ``Docpie`` checks if the keys in
   ``Docpie.extra`` appears in ``argv``.
7. if it finds the key, to say ``-v`` for example, ``Docpie`` will check
   ``Docpie.extra`` and call ``Docpie.extra["-v"](docpie, "-v")``, the
   first argument is the ``Docpie`` instance.
8. By default, ``Docpie.version_handler(docpie, flag)`` will print
   ``Docpie.version``, and exit the program.

for ``help=True``, ``Docpie`` will check "--help" and "-h", then set
value as ``Docpie.help_handler``.

extra
^^^^^

You can costomize this by passing ``extra`` argument, e.g.

.. code:: python

    """
    Example for Docpie!

    Usage: example.py [options]

    Options:
      -v, --obvious    print more infomation  # note the `-v` is here
      --version        print version
      -h, -?, --help   print this infomation
      --moo            the Easter Eggs!

    Have fun, my friend.
    """
    from docpie import Docpie
    import sys


    def moo_handler(pie, flag):
        print("Alright you got me. I'm an Easter Egg.\n"
              "You may use this program like this:\n")
        print("Usage:")
        print(pie.usage_text)
        print("")
        print("Options:")
        print("".join(pie.option_text.splitlines(True)[:-1]))
        sys.exit()    # Don't forget to exit

    pie = Docpie(__doc__, version='0.0.1')
    pie.set_config(
      extra={
        '--moo': moo_handler,  # set moo handler
      }
    )

    print(pie)

now try the following command:

.. code:: bash

    example.py -v
    example.py --version
    example.py -h
    example.py -?
    example.py --help
    example.py --moo

set\_auto\_handler
^^^^^^^^^^^^^^^^^^

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
    print(pie.docpie())

Then ``Docpie`` will handle both ``-m`` & ``--moo``.

to customize your ``extra``, the following attribute of ``Docpie`` may
help:

-  ``Docpie.version`` is the version you set. (default ``None``)
-  ``Docpie.usage_text`` is the usage section. ("Usage:" is not
   contained)
-  ``Docpie.option_text`` is the options section. ("Options:" is not
   contained)

Serialization
~~~~~~~~~~~~~

``Docpie.need_pickle(self)`` give you everything you need to pickle.
``Docpie.restore_pickle(value)`` restore everything which is already
converted back by pickle

``Docpie.convert_2_dict(self)`` can convert ``Docpie`` instance into a
dict so you can JSONlizing it. Use ``Docpie.convert_2_docpie(cls, dic)``
to convert back to ``Docpie`` instance.

**Note:** if you change ``extra`` directly or by passing ``extra``
argument, the infomation will be lost because JSON can not save function
object. You need to call ``set_config(extra={...})`` after
``convert_2_docpie``.

Here is a full example of serialization and unserialization together
with ``pickle``

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
        pickle.dump(pie.need_pickle(), pkf)

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
                pie = Docpie.restore_pickle(pickle.load(pkf))
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

Difference
----------

``docpie`` is not ``docopt``.

1. ``docpie`` will trade element in ``[]`` (optional) as a whole, e.g

   .. code:: python

       doc = '''Usage: prog [a a]...'''
       print(docpie(doc, 'prog a'))  # Exit
       print(docpie(doc, 'prog a a'))  # {'a': 2}

   Which is equal to ``Usage: prog [(a a)]...`` in ``docopt``.

2. In ``docpie`` if one mutually exclusive elements group matches, the
   rest groups will be skipped

   .. code:: python

       print(docpie('Usage: prog [-vvv | -vv | -v]', 'prog -vvv'))  # {'-v': 3}
       print(docpie('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # Fail
       print(docopt('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # {'-v': 3}

3. In ``docpie`` you can not "stack" option and value in this way even
   you specify it in "Options":

   .. code:: python

       """Usage: prog -iFILE   # Not work in docpie

       Options: -i FILE
       """

   But you can do it in this way:

   .. code:: python

       """Usage: prog -i<FILE>

       Options: -i <FILE>
       """

4. ``docpie`` uses ``Options:`` to find the current "Option" section,
   however ``docopt`` treats any line in ``doc`` that starts with ``-``
   (not counting spaces) as "Options"

5. Subparsers are not supported currently.

Known Issues
------------

Currently, ``docpie`` can support arguments after repeated argument, but
this feature has a very strict limit.

::

    Usage: cp.py <source_file>... <target_directory> [-f] [-r]

1. the repeated argument should be and only be one ``ARGUMENT``, which
   means:

-  YES: ``(<arg1>)... <arg2> <arg3>``
-  YES: ``[<arg1]... <arg2>``
-  NO: ``(<arg1> <arg2>)... <arg3>``
-  NO: ``-a... -a``
-  NO: ``cmd... cmd``

2. the elements that can "borrow" values from the repeatable argument
   can only be ``ARGUMENT`` (even can not be grouped by ``()`` or
   ``[]``)

-  ``<arg1>... <arg1> <arg2> command``: the ``command`` can't "borrow"
   value from ``<arg1>``, it won't match ``val1 val2 val3 command``
-  ``<arg1>... (<arg2>)`` won't work,

Developing
----------

execute ``/test/test.py`` to run the test

the logger name of ``docpie`` is ``"docpie"``

``docpie`` contains two developing tools: ``bashlog`` and ``tracemore``.
You can do like:

.. code:: python

    from docpie import docpie, Docpie, bashlog
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
