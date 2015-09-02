## 0.0.6

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
