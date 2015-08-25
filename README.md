# docpie

This project is aimed to provide a more powerful command-line interface for
your python program, by simply providing `__doc__` string.

If you want something more light-weight, you may have a look at [python-docopt](https://github.com/docopt/docopt)

## Installation

```bash
pip install git+git://github.com/TylerTemp/docpie.git
```
`docopt` has been tested with Python:

2.6.6, 2.6.9, 2.7, 2.7.10,

3.2, 3.3.0, 3.3.6, 3.4.0, 3.4.3,

pypy-2.0, pypy-2.6.0, pypy3-2.4.0


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
