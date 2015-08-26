docpie
===============================================================================

Intro
-------------------------------------------------------------------------------

Isn't it brilliant how [python-docopt](https://github.com/docopt/docopt)
parses the `__doc__` and converts command line into python dict? `docpie` does
the similar work, but...

**`docpie` can do more!**

If you have never used `docpie` or `docopt`, try this. It can parse your
command line according to the `__doc__` string:

```python
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
```

Then try `$ python example.py ship Titanic move 1 2` or
`$ python example.py --help`, see what you get.

**`docpie` can do...**

`docpie` has some useful and handy features, e.g.

1.   it allow you to specify the program name.

    ```python
    '''Usage:
      myscript.py rocks
      $ python myscript.py rocks
      $ sudo python myscript.py rocks
    '''
    print(docpie(__doc__, name='myscript.py'))
    ```

2.  Different from `docpie, `docpie` will handle `--` automatically by
    default, you do not need to write it in your "Usage:" anymore.
    (You can also trun off this feature)

    ```python
    '''Usage:
     prog <hello>
    '''
    from docpie import docpie
    print(docpie(__doc__))
    ```

    Then `$ python example.py test.py -- --world` will give you
    `{'--': True, '<hello>': '--world'}`

3.  Some issues in `docopt` have been solved in `dopie` (e.g.
    [#71](https://github.com/docopt/docopt/issues/71),
    [#282](https://github.com/docopt/docopt/issues/282),
    [#130](https://github.com/docopt/docopt/issues/130))

    ```python
    '''
    Usage:
     test.py [ --long-option ]
       -o <value>  (-a | -b)

    Options:
     --long-option    Some help.
     -a               Some help.
     -b               Some help.
     -o <value>       Some help.
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
    ```

    output:

    ```bash
    $ python test.py -o sth -a
    ---- docopt ----
    -o is specified ambiguously 2 times
    ---- docpie ----
    {'--': False,
     '--long-option': False,
     '-a': True,
     '-b': False,
     '-o': 'sth'}
    ```

   <!-- `docopt` allows you to customize some flags' behavior, e.g

   ```python
   '''
   A simple example

   Usage:
     text.py [options]

   Options:
     -h, --help  print this message
   '''

   import sys
   from docopt import docopt

   def handle_short_help(docpie, flag):
       print('Usage:')
       print(docpie.usage_text)
       print("Try '%s --help' for more information." % (docpie.name or sys.argv[0]))
       sys.exit()

   argument = docpie(__doc__, extra={'-h': handle_short_help})
   print(argument)
   ```

   Now `-h` will display the "Usage" with a tip, `--help` will print the whole
   `__doc__` string -->


Installation
-------------------------------------------------------------------------------

```bash
pip install git+git://github.com/TylerTemp/docpie.git
```

`docopt` has been tested with Python:

2.6.6, 2.6.9, 2.7, 2.7.10,

3.2, 3.3.0, 3.3.6, 3.4.0, 3.4.3,

pypy-2.0, pypy-2.6.0, pypy3-2.4.0


Basic Usage
-------------------------------------------------------------------------------

```python
from docpie import docpie
```

```python
docpie(doc, argv=None, help=True, version=None,
       stdopt=True, attachopt=True, attachvalue=True,
       auto2dashes=True, name=None, case_sensitive=False, extra={})
```

Note that it's strongly suggested that you pass keyword arguments instead of
positional arguments.

*   `doc` is the description of your program which `docpie` can parse. It's
    usually the `__doc__` string of your python script, but it can also be any
    string in corrent format. The format is given in next section. Here is an
    example:

    ```python
    """
    Usage: my_program.py [-hso FILE] [--quiet | --verbose] [INPUT ...]

    Options:
     -h --help    show this
     -s --sorted  sorted output
     -o FILE      specify output file [default: ./test.txt]
     --quiet      print less text
     --verbose    print more text
    """
    ```

*   `argv` (sequence) is the command line your program accepted and it should
    be a list or tuple. By default `docpie` will use `sys.argv` if you omit
    this argument when it's called.
*   `help` (bool, default `True`) tells `docpie` to handle `-h` & `--help`
    automatically. When it's set to `True`, `-h` will print "Usage" and "Option"
    section, then exit; `--help` will print the whole `doc`'s value and exit.
    set `help=False` if you want to handle it by yourself. Use `extra` (see
    below) or see `Docpie` if you only want to change `-h`/`--help` behavior.
*   `version` (any type, default `None`) specifies the version of your program.
    When it's not `None`, `docpie` will handle `-v`/`--version`, print this
    value, and exit. See `Docpie` if you want to customize it.
*   `stdopt` (bool, default `True`) when set `True`(default), long flag should
    only starts with `--`, e.g. `--help`, and short flag should be `-` followed
    by a letter. This is suggested to make it `True`. When set to `False`,
    `-flag` is also a long flag. Be careful if you need to turn it off.
*   `attachopt` (bool, default `True`) allow you to write/pass several short
    flag into one, e.g. `-abc` can mean `-a -b -c`. This only works when
    `stdopt=True`

    ```python
    from docpie import docpie
    print(docpie('''Usage: prog -abc''', ['prog', '-a', '-bc']))
    # {'--': False, '-a': True, '-b': True, '-c': True}
    ```

*   `attachvalue` (bool, default `True`) allow you to write short flag and its
    value together, e.g. `-abc` can mean `-a bc`. This only works when
    `stdopt=True`

    ```python
    '''
    Usage:
      prog [options]

    Options:
      -a <value>  -a expects one value
    '''
    from docpie import docpie
    print(docpie(__doc__, ['prog', '-abc']))
    # {'--': False, '-a': 'bc'}
    ```

*   `auto2dashes` (bool, default `True`) When it's set `True`, `docpie` will
    handle `--` (which means "end of command line flag", see
    [here](http://www.cyberciti.biz/faq/what-does-double-dash-mean-in-ssh-command/)
    )

    ```python
    from docpie import docpie
    print(docpie('Usage: prog <file>'), ['prog', '--', '--test'])
    # {'--': True, '<file>': '--test'}
    ```

*   `name` (str, default `None`) is the "name" of your program. In each of your
    "usage" the "name" will be ignored. By default `docpie` will ignore the
    first element of your "usage"
*   `case_sensitive` (bool, default `False`) specifies if it need case
    sensitive when matching "Usage:" and "Options:"

the return value is a dictonary. Note if a flag has alias(e.g, `-h` & `--help`
has the same meaning, you can specify in "Options"), all the alias will also
in the result.

Format
-------------------------------------------------------------------------------

`docpie` is indent sensitive.

### Usage Format

"Usage" starts with `Usage:`(set `case_sensitive` to make it case
sensitive/insensitive), ends with a *visibly* empty line.

```python
"""
Usage: program.py

"""
```

You can write more than one usage patterns

```python
"""
Usage:
  program.py <from> <to>...
  program.py -s <source> <to>...

"""
```

When one usage pattern goes too long you can separate into several lines,
but the following lines need to indent more:

```python
"""
Usage:
    prog [--long-option-1] [--long-option-2]
         [--long-option-3] [--long-option-4]  # Good
    prog [--long-option-1] [--long-option-2]
      [--long-option-3] [--long-option-4]  # Works but not so good
    prog [--long-option-1] [--long-option-2]
    [--long-option-3] [--long-option-4]  # Not work. Need to indent more.

"""
```

Each pattern can consist of the following elements:

*   **&lt;arguments&gt;**, **ARGUMENTS**. Arguments are specified as either
    upper-case words, e.g. `my_program.py CONTENT-PATH` or words
    surrounded by angular brackets: `my_program.py <content-path>`.
*   **--options**. Short option starts with a dash(`-`), followed by a
    character(`a-z`, `A-Z` and `0-9`), e.g. `-f`. Long options starts with two
    dashes (`--`), followed by seveval characters(`a-z`, `A-Z`, `0-9` and `-`),
    e.g. `--flag`. When `stdopt` and `attachopt` are on, you can "stack"
    seveval of short option, e.g. `-oiv` can mean `-o -i -v`.

    The option can have value. e.g. `--input=FILE`, `-i FILE`, 

Difference
-------------------------------------------------------------------------------

`docpie` is not `docopt`.


1.  `docpie` will trade element in `[]` (optional) as a whole, e.g

    ```python
    doc = '''Usage: prog [a a]...'''
    print(docpie(doc, 'prog a'))  # Exit
    print(docopt(doc, 'prog a a'))  # {'a': 2}
    ```

    Which is equal to `Usage: prog [(a a)]...` in `docopt`.

2.  In `docpie` if one mutually exclusive elements group matches, the rest
    groups will be skipped

    ```python
    print(docpie('Usage: prog [-vvv | -vv | -v]', 'prog -vvv'))  # {'-v': 3}
    print(docpie('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # Fail
    print(docopt('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # {'-v': 3}
    ```

3.  In `docpie` you can not "stack" option and value in this way
    even you specify it in "Options":

    ```python
    """Usage: prog -iFILE

    Options: -i FILE
    """
    ```

    But you can do it in this way:

    ```python
    """Usage: prog -i<FILE>

    Options: -i <FILE>
    """
    ```

## Known issue

the following situation:

```
Usage: --long=<arg>
```

without announcing `Options` will match `--long sth` and `sth --long`. To
avoid, simply write an announcement in `Options`

```
Usage: --long=<arg>

Options:
 --long=<sth>    this flag requires a value
```

## More features

This feature can be expected in the future `docpie`

(Not support currently)

```
Usage: cp.py <source_file>... <target_directory>
```
