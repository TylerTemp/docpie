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
