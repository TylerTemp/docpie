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

2.  Different from `docpie, `docpie` will handle `-` and `--` automatically by
    default, you do not need to write it in your "Usage:" anymore.
    (You can also trun off this feature)

    ```python
    '''Usage:
     prog <hello>
    '''
    from docpie import docpie
    print(docpie(__doc__))
    ```

    Then `$ python example.py test.py - -- --world` will give you
    `{'-': True, '--': True, '<hello>': '--world'}`

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
    {'-': False,
    '--': False,
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


Usage
-------------------------------------------------------------------------------

### `docpie` ###

```python
from docpie import docpie
```

```python
docpie(doc, argv=None, help=True, version=None,
       stdopt=True, attachopt=True, attachvalue=True,
       autodash=True, auto2dashes=True, name=None, extra={})
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
    `-flag` is also a long flag. Be careful if you need to trun it off.
*   `attachopt` (bool, default `True`)


## Difference

`docpie` is not `docopt`.


1. `docpie` will trade element in `[]` (optional) as a whole, e.g

   ```python
   doc = '''Usage: prog [a a]...'''
   print(docpie(doc, 'prog a'))  # Exit
   print(docopt(doc, 'prog a a'))  # {'a': 2}
   ```

   Which is equal to `Usage: prog [(a a)]...` in `docopt`.

2. In `docpie` if one mutually exclusive elements group matches, the rest
   group will be skipped

   ```python
   print(docpie('Usage: prog [-vvv | -vv | -v]', 'prog -vvv'))  # {'-v': 3}
   print(docpie('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # Fail
   print(docopt('Usage: prog [-v | -vv | -vvv]', 'prog -vvv'))  # {'-v': 3}
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
