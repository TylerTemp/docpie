## TODO

*   Refactory
*   Add a bash auto-complete tool [#2](https://github.com/TylerTemp/docpie/issues/2)
*   Document needs a better organization

## 0.3.1

*   [new] Add `namedoptions` feature. [Document](https://github.com/TylerTemp/docpie/wiki/Advanced-APIs#namedoptions)

## 0.3.0

*   [fix] can't parse options expecting arguments in usage
    correctly, due to a previous code changing

        """
        Usage: prog [options] --color <COLOR>

        Options:
            --color=<COLOR>
        """
        from docpie import docpie
        print(docpie(__doc__), ['prog', '--color', 'red'])
        # {'--': False, '--color': 'red'}

## 0.2.9

*   [fix] `optionsfirst` can work as expected (previously it can not recognize the
    expected arguments of a option and lead to fail):

        """
        Usage: prog [options] -w<val> <arg>
        """
        from docpie import docpie
        print(docpie(__doc__), ['prog', '-w', 'sth', 'arg'], optionsfirst=True)
        # {'--': False, '-w': 'sth', '<arg>': 'arg'}

## 0.2.8

*   [fix] the following situation will not failed now (note: not recommended, not POSIX standard)

        """
        Usage: prog [options] <arg>

        Options:
            --force[=<value>]
        """

        from docpie import docpie
        docpie(__doc__, ['prog', '--force', '--', 'val'])
        # {'--': True, '--force': None, '<arg>': 'val'}


## 0.2.7

*   [fix] a typo which will cause failed to throw an error when there is
    an syntax error in your help message
*   \[fix\] [issue #3](https://github.com/TylerTemp/docpie/issues/3)

## 0.2.6

*   [new] Now repeatable arguments have a better handling way.

    First, the repeatable elements can be more than one argument,
    and can be nested. But can only be argument (not option, not
    command)

    ```
    (<arg1> <arg2>)... <arg3>
    ```

    Second, the elements after repeatable arguments can be argument
    and command, and can be groupd

    ```
    <arg>... <arg2> cmd
    <arg>... (cmd <arg2>) <arg3>
    ```

## 0.2.5

*   [fix] When "Usage" section contains "Options:"
    (e.g. "`prog <options:>`"), it won't be parsed as "Option" section

## 0.2.4

*   [fix] Support windows style line separator `/r/n`

## 0.2.3

*   [fix] when "Usage" stack as `-a<val>` and "Options"
    annouced as `-a <val>    an option` it will raise an error

## 0.2.2

*   [fix] a bug in test that some tests will not report when they
    fail
*   [fix] `help` & `version` won't work because of the previous refactor

## 0.2.1

*   [fix] stdopt/attachopt/attachvalue in `set_config`
    will re-init the `Docpie` instance
*   [fix] ``<a|b>`` will not be parsed as ``<a | b>`` now.

## 0.2.0

*   [new] `appearedonly` argument to allow only show use inputted options
    (only options, won't affect commands/arguments)
*   [new] multi options section support. Now you can write several options like:

    ```
    Usage: git <cmd> [options] [<args>...]

    Global Options:
        -h, --help      print this message
    rm Options:  # seperate with options by breaking the line
        -f, --force     force remove a file

    add Options:  # seperate with at least one visable line
        -n, --dry-run  Don't actually add the file(s)
    ```

## 0.1.1

*   [change] use "Options" when parsing "Usage" and remove some `fix` method

    Though it's not recommended, you can now write:

    ```
    Usage: prog -iFILE

    Options: -i FILE    input file
    ```

    It's not clear. You'd better write `-i<file>` instead.

*   [new] notice user when a flag is not defined.('Unknown option: <option>')
*   [fix] handle auto_handler before matching
*   [new] `optionsfirst` argument
*   [change] **break-change** remove `Docpie.option_text` attribute,
    add `Docpie.option_sections`

## 0.1.0

*   [fix] merging value bug. `Usage: prog [--repeat=<sth> --repeat=<sth>]`
    matching `prog` will now give `'--repeat=[]'` instead of the old
    wrong value `'--repeat=0'`

## 0.0.9

*   [new] better error information notification.
*   [fix] better `Either` handling. Now `Either` will be expanded and throwed
    away. Which means now for

    ```
    Usage: prog [-v | -vv | -vvv] cmd
    ```

    can match `-v cmd`, `-vv cmd`, `-vvv cmd`. The old format also works

    ```
    Usage: prog [-vvv | -vv | -v] cmd
    ```

    but the new one is more readable.
*   [fix] remove some old api, remove `save.py`


## 0.0.8

*   [fix] `Docpie.tokens.Argv.auto_expand` handles `--` in a wrong way

## 0.0.7

*   [new] Now `Docpie` can guess your long options. e.g. when you write both
    `--verbose` & `--version`, then the `--verb` in argv will be interpreted
    as `--verbose`, `--vers` as `--version`, the `--ver` will raise an error.

## 0.0.6

### 1441214390.257887

*   [fix] `Docpie` will try to push all options ahead. It fixed
    `test.test_docpie.DocpieRunDefaultTest.test_option_unit_stack`

### 1441188808.780277

*   [change] now Docpie.option_text will be exactly the same as the
    "Option" section (contains "Option" title).
*   [change] now Docpie.usage_text will be exactly the same as the
    "Usage" section (contains "Usage" title).
*   [change] Change the data storage to `Docpie` instance, now you can
    initialize several `Docpie` instances in one program with different configurations.
*   [change] Allow `pickle` the `Docpie` instance directly.
    Deprecate `need_pickle` & `restore_pickle`

## 0.0.5

*   [change] **break-change**: `[]` means anything in it is optional.

    ```
    Usage: prog [-dir]
    ```

    equals to

    ```
    Usage: prog [-d] [-i] [-r]
    ```

    If you want all elements to appear, use

    ```
    Usage: prog [(-dir)]
    ```

## 0.0.4

*   [fix] `Usage: prog [-v] -- <args>...` failed to match `porg -v -- -v --verb`
*   [fix] [#1](https://github.com/TylerTemp/docpie/issues/1) command order bug.
