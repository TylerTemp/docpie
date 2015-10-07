.. docpie
.. README.rst

docpie
======

`一个简单而Pythonic的方式创建POSIX标准命令行接口`

查看: `主页 <http://docpie.comes.today>`__ /
`GitHub <https://github.com/TylerTemp/docpie/>`__ /
`PyPi <https://pypi.python.org/pypi/docpie>`__

.. contents::

日志
---------

版本 0.2.1:

-   [修正] ``set_config`` 修改 ``stdopt`` / ``attachopt`` / ``attachvalue``
    会导致重新初始化实例，从而保证解析的正确性。

`完整更新日志 <https://github.com/TylerTemp/docpie/blob/master/CHANGELOG.md>`__



简介
------------


`python-docopt <https://github.com/docopt/docopt>`__ 通过定义的
``__doc__``来把命令行参数转换为python dict的方式简直碉堡！``docpie``
做的差不多，但是……

**docpie更强大！**

如果你还没用过 ``docpie`` 或者 ``docopt`` ，试试这个。它可以根据``__doc__``
字符串解析命令行：

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

`在线试试 >> <http://docpie.comes.today/try/?example=ship>`__

然后试试运行 ``$ python example.py ship Titanic move 1 2`` 或者
``$ python example.py --help`` 吧！

**docpie可以做到……**

``docpie`` 有更多方便好使的特性，比如：

1. 指定程序名称

   .. code:: python

       '''Usage:
         myscript.py rocks
         $ python myscript.py rocks
         $ sudo python myscript.py rocks
       '''
       print(docpie(__doc__, name='myscript.py'))

   `在线试试
   >> <http://docpie.comes.today/try/?example=myscript.py>`__

2. 不同于 ``docopt`` ， ``docpie`` 默认自动处理 ``--`` ，你不需要再在"Usage:"
   里面啰嗦啦！（你也可以关闭这个特性）

   .. code:: python

       '''Usage:
        prog <hello>
       '''
       from docpie import docpie
       print(docpie(__doc__))

   `在线试试 >> <http://docpie.comes.today/try/?example=helloworld>`__

   这样如果运行 ``$ python example.py test.py -- --world`` 就会得到
   ``{'--': True, '<hello>': '--world'}``

3. 一些 ``docopt`` 的问题并不存在于 ``dopie`` （在线试试`#71
   >> <http://docpie.comes.today/try/?example=opt71>`__, `#282
   >> <http://docpie.comes.today/try/?example=opt282>`__, `#130
   >> <http://docpie.comes.today/try/?example=opt130>`__, `#275
   >> <http://docpie.comes.today/try/?example=opt275>`__, `#209
   >> <http://docpie.comes.today/try/?example=opt209>`__）

   **注意**: 关于这个特性的限制请查看"已知问题"章节。

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

   输出：

   .. code:: bash

       $ python mycopy.py ./docpie/*.py ./docpie/test/*.py ~/my_project ~/config.cfg
       ---- docopt ----
       Usage: mycopy.py <source_file>... <target_directory> <config_file>
       ---- docpie ----
       {'--': False,
        '<config_file>': '/Users/tyler/config.cfg',
        '<source_file>': ['./docpie/setup.py', './docpie/test/*.py'],
        '<target_directory>': '/Users/tyler/my_project'}

   `在线试试 >> <http://docpie.comes.today/try/?example=mycopy.py>`__

安装
------------

安装发布版:

.. code:: python

    pip install docpie

安装测试版:

.. code:: bash

    pip install git+git://github.com/TylerTemp/docpie.git

``docpie`` 已经在以下Python版本中测试过：

2.6, 2.7

3.2, 3.3, 3.4, 3.5

pypy-2.0, pypy-2.6, pypy3-2.4

基本用法
-----------

.. code:: python

    from docpie import docpie

你可以在 `主页 <http://docpie.comes.today>`__ 查看快速导览。

API
~~~

.. code:: python

    docpie(doc, argv=None, help=True, version=None,
           *,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, ...)

``docpie`` 接受一个必选参数，3个可选参数和几个关键字参数。

-  ``doc`` 是 ``docpie`` 拿去解析的字符串。它通常为你脚本的 ``__doc__`` 字符串，当然
   任何格式正确的字符串都是可以的。格式要求请参见下一章，这里是一个快速示例：

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

   `在线试试 >> <http://docpie.comes.today/try/?example=docexample>`__

-  ``argv`` （序列）即为你程序接受到的命令行参数，推荐列表或元组。默认使用 ``sys.argv`` 。
-  ``help`` （ 布尔，默认  ``True``  ）指明 ``docpie`` 自动处理 ``-h`` 和
   ``--help``参数。默认处理方式是，对于``-h``打印"Usage"和"Option"章节，而 ``--help``
   则打印整个传入的 ``doc`` 值，打印完毕推出程序。如果你想自己处理，设置为 ``False`` 即可。
   需要自定义的话可以参见“高级用法”-“自动处理”章节。
-  ``version`` （任何类型，默认 ``None`` ）用来指出你程序的版本。当该值不为 ``None`` 时，
   ``docpie`` 将自动处理 ``-v`` / ``--version`` 参数。默认为打印该值后退出程序。参见
   “高级用法”-“自动处理”章节修改默认处理方法。
-  ``auto2dashes`` （布尔，默认 ``True`` ）。为 ``True`` 时将自动处理 ``--`` （命令行
   option结束标志，参见 `这里 <http://www.cyberciti.biz/faq/what-does-double-dash-mean-in-ssh-command/>`__）
   。

   .. code:: python

       from docpie import docpie
       print(docpie('Usage: prog <file>'), ['prog', '--', '--test'])
       # {'--': True, '<file>': '--test'}

   `在线试试 >> <http://docpie.comes.today/try/?example=testfile>`__

-  ``name`` （字符串，默认 ``None`` ）为你程序的名字。“Usage”中第一个 ``name`` 会被忽略掉。
   默认忽略所有“Usage”中的第一个元素。
-  ``optionsfirst`` （布尔，默认 ``False`` ）。设为 ``True`` 则在第一个positional元素后
   的所有元素都将被视为positional参数。

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

   这个特性可以帮助你包装其它程序命令行参数。请参见例子
   `example-get <https://github.com/TylerTemp/docpie/tree/master/docpie/example/git>`__

-  ``...`` 其它参数请参见“高级用法” - “API”

函数返回一个 ``dict`` 对象。注意所有option的别名（你可以在“Options”中指定）都将出现在结果中。

格式
~~~~~~

``docpie`` 靠缩进和换行区分内容。

Usage格式
^^^^^^^^^^^^

"Usage" 用 ``Usage:`` 打头（大小写不敏感）。如果有其它部分，用一个空行隔开。

.. code:: python

    """
    Usage: program.py

    This line is not part of usage.
    """

你可以写多条“Usage”

.. code:: python

    """
    Usage:
      program.py <from> <to>...
      program.py -s <source> <to>...
    """

`在线试试 >> <http://docpie.comes.today/try/?example=from_to>`__

你还可以将单个“Usage”分行，但分拆的行需要更多缩进以示区别。

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

每条定义由以下元素构成：

-  **<arguments>**，**ARGUMENTS**。 Arguments为全大写字母
   （例如 ``my_program.py CONTENT-PATH`` ）或者用尖括号括起来
   （例如 ``my_program.py <content-path>`` ）。
-  **--options**。短option用短横线（ ``-`` ）开始，后接一个字符
   （ ``a-z`` ， ``A-Z`` 和 ``0-9`` ），例如 ``-f`` 。长option用两根短横线（ ``--`` ）开始，后
   接几个字符（ ``a-z`` ， ``A-Z`` ， ``0-9`` 和 ``-`` ），例如 ``--flag`` 。你可以将多个
   短option写在一起，例如用 ``-oiv`` 表示 ``-o -i -v`` 。

   option可以接受参数，例如］ ``--input=FILE`` 、 ``-i FILE`` 、 ``-i<file>`` 。
   推荐在“Options”中写明。
-  **commands**。不遵循以上参数的单词均为 ``command`` 。注意 ``-`` 和 ``--`` 也是 ``command``

定义规则的符号：

-  **[ ]** （方括号） **可选** 元素。可选元素并非必须全部出现。
   ``program.py [-abc]`` 等于 ``program.py [-a] [-b] [-c]`` 。
-  **( )** （圆括号） **必须** 元素。默认不在方括号中的都为必选元素。
   ``my_program.py --path=<path> <file>...`` 等同于
   ``my_program.py (--path=<path> <file>...)`` 。
-  **\|** （竖线） **排他** 元素。用 **( )** 或者 **[ ]**
   来建立排他组，例如 ``program.py (--left | --right)`` 。注意argument彼此并没有
   区别，因此 ``program.py (<a> | <b> | <c>)`` 会将  ``<a>`` ，
   ``<b>`` 和 ``<c>`` 视为同名argument，例如：

   .. code:: python

       from docpie import docpie
       print(docpie('Usage: prog (<a> | <b>)', 'prog py'.split()))
       # {'--': False, '<a>': 'py', '<b>': 'py'}

   `在线试试
   >> <http://docpie.comes.today/try/?example=either_args>`__

-  **...** （省略号） **重复** 元素。意味着前面的元素（组）可以输入多次，
   例如 ``my_program.py FILE ...`` 意味着可以接受一个或多个
   ``FILE`` 。如果你需要匹配零个或多个，使用方括号： ``my_program.py [FILE ...]`` 。
   这个元素为一元符号，仅对左边的元素（组）有效。
-  **[options]** （大小写敏感）所有定义在“options”中的option占位符。这个符号意味着
   所有定义在“options”中的option都可以在这条“Usage”中使用。

   注意，你可以写形如 ``program.py [options]...`` 的格式，但不可以写
   ``program.py [options...]`` （这里 ``option`` 会被解释为argument）

注意你可以将多个短option写为一个，例如 ``-abc`` 等于 ``-a -b -c`` 。

.. code:: python

   from docpie import docpie
   print(docpie('''Usage: prog -abc''', ['prog', '-a', '-bc']))
   # {'--': False, '-a': True, '-b': True, '-c': True}

`在线试试 >> <http://docpie.comes.today/try/?example=attachopt>`__

你也可以将短option的参数与option写在一起。

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

`在线试试
>> <http://docpie.comes.today/try/?example=attachvalue>`__

你还可以指定某个元素允许多次出现：

::

    Usage: my_program.py [-v | -vv | -vvv]

`在线试试
>> <http://docpie.comes.today/try/?example=exclusive_good>`__

这样的话输入的 ``-v`` 会被计数。如果输入 ``my_program -vv`` ，则 ``-v`` 的解析结果
为2。option/command均可以使用这个语法。

而对于argument和接受argument的option，这个语法会触发收集，
相同参数的值会被收集为一个列表：

::

    Usage: program.py <file> <file> --path=<path>...


`在线试试 >> <http://docpie.comes.today/try/?example=same_name>`__

（建议定义“options”区指明 ``--path`` 要求argument）

如果输入 ``program.py file1 file2 --path ./here ./there`` 就会得到
``{'<file>': ['file1', 'file2'], '--path': ['./here', './there']}``

记住 ``...`` 仅影响左边最近的 ``<path>`` 。下面的定义方法要求输入的格式不一样：

::

    Usage: program.py <file> <file> (--path=<path>)...

`在线试试
>> <http://docpie.comes.today/try/?example=same_name_repeat_option>`__

它可以匹配
``program.py file1 file2 --path=./here --path=./there`` ，结果相同。

Options格式
^^^^^^^^^^^^^^

**Option描述区** 列出了可用的option。

在这个区域你可以定义：

-  长短option的别名
-  option是否要求参数
-  option是否有默认值

“Options”开始于 ``Options:`` （大小写不敏感）。option的描述可以空两格写，
也可以换行写。

用一个空行来区分本部分与其它部分，例如：

.. code:: python

    """
    Usage: prog [options]

    Options: -h"""

或者

.. code:: python

    """
    Usage: prog [options]

    Options:
      -h, --help

    Not part of Options.
    """

你可以定义多个“options”区域，但不会有什么特别的效果。

::

    Global Options:
      -h, --help           print this message
      -v, --verbose        give more infomation
    Comment Options:
      -m, --message=<msg>  add message for comment

“options”章节的格式如下：

-  如果option接受参数，应该用一个空格隔开。对于长option推荐使用等号（ ``=`` ）隔离。
   option彼此用一个空格，或者一个逗号，或者逗号加空格隔开。

   ::

       -o FILE --output=FILE       # without comma, with "=" sign
       -i <file>, --input <file>   # with comma, without "=" sing

   你可以指定多个别名（仅推荐在以下情况使用）

   ::

       -?, -h, --help

-  option描述有两种写法：

   1) 写在同一行，用至少两格空格隔开。
   2) 另起一行，但要至少多缩进两格空格。

   ::

       -?, -h, --help  print help message. use
                       -h/-? for a short help and
                       --help for a long help. # Good. 2+ empty spaces
       -a, --all
           A long long long long long long long
           long long long long long description of
           -a & --all    # Good. New line & indent 2 more spaces

   `在线试试
   >> <http://docpie.comes.today/try/?example=option_format>`__

-  用 ``[default: 默认值]`` 来指定option默认值。注意这个格式要求很严格：
   起始于 ``[default:`` ，加个空格，加上你的默认值，结束于 ``]`` 。
   把这个放在描述末位即可。注意后面不能加任何东西（句号，空格都也不行）

   ::

       --coefficient=K  The K coefficient [default: 2.95]  # '2.95'
       --output=FILE    Output file [default: ]            # empty string
       --directory=DIR  Some directory [default:  ]        # a space
       --input=FILE     Input file[default: sys.stdout].   # not work because of the dot

   `在线试试
   >> <http://docpie.comes.today/try/?example=example_default>`__

-  可重复option的默认值会按照空白符拆解为一个列表。

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

   `在线试试
   >> <http://docpie.comes.today/try/?example=repeat_default>`__

虽然这个不是POSIX标准，但 ``docopt`` 支持如下语法（不推荐使用）：

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

`在线试试
>> <http://docpie.comes.today/try/?example=non_posix_option>`__

高级用法
--------------

通常 ``docpie`` 和基本参数就够了，但你可以用其它参数和 ``Docpie`` 类做更多事儿。

.. code:: python

    from docpie import Docpie

基本
~~~~~

当使用

.. code:: python

    from docpie import docpie
    print(docpie(__doc__))

等同于

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

没介绍的参数如下：

-  ``stdopt`` （布尔，默认 ``True`` ，**实验参数**)当设为 ``True`` 时，长option必须
   以 ``--`` 开头，例如 ``--help`` ；短option必须以 ``-`` 开始。若设为 ``False`` ，则
   ``-flag`` 也会被解析为长option。（ ``find`` 之类的老程序使用这种格式。）
-  ``attachopt`` （布尔，默认 ``True`` , **实验参数**）允许你将多个短option写为
   一个，例如 ``-abc`` 等于 ``-a -b -c`` 。仅在 ``stdopt=True`` 时有效。
-  ``attachvalue`` 布尔，默认 ``True`` , **实验参数**）允许你将短option和它的值写在一起，
   例如 ``-abc`` 等于 ``-a bc`` 。仅在 ``stdopt=True`` 时有效。
-  ``case_sensitive`` （布尔，默认 ``False`` ）指明匹配"Usage:"和"Options:"时是否
   大小写敏感。
-  ``appearedonly`` （布尔，默认 ``False`` ）。当设为 ``True`` 时，
   ``docpie`` 不会将为出现在 ``argv`` 中的option加入结果。考虑以下情况：

   ::

      Usage: prog [options]

      Options:
         -s, --sth=[<value>]    Just an example. Not POSIX standard

   我们无法从结果 ``{'-s': None, '--sth': None}`` 中看出用户是输入了 ``--sth``
   还是什么都没输入。如果 ``appearedonly=True`` ，则对于用户根本没输入 ``--sth``
   时，结果中一定没有 ``--sth`` 这个值。注意： 1. 这不是POSIX标准。 2. 仅对
   option有效。
-  ``extra`` 见下部分。

.. code:: python

    Docpie(doc=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, appearedonly=False, extra={})

``Docpie`` 接受除了 ``argv`` 的所有 ``docpie`` 参数。

.. code:: python

    pie = Docpie(__doc__)
    pie.docpie(argv=None)

``Docpie.docpie`` 接受 ``docpie`` 同样要求的 ``argv`` 。


修改配置
~~~~~~~~~~~~~~~~~~~~

.. code:: python

    Docpie.set_config(self, **config)

``set_config`` 允许你在实例化 ``Docpie`` 后更改配置。要求参数与初始化参数一致，除了不接受
``doc`` 参数。

注意，修改 ``stdopt`` / ``attachopt`` / ``attachvalue`` 会导致重新初始化实例，你应该
新初始化一个``Docpie``对象，而非修改这三个参数。

.. code:: python

    pie = Docpie(__doc__)
    pie.set_config(help=False)  # now Docpie will not handle `-h`/`--help`
    pie.docpie()

自动处理
~~~~~~~~~~~~

Docpie的 ``extra`` 属性为一个字典，键为一个option（字符串），值为一个可回调对象。
可回调对象需要接受两个参数：第一个为 ``Docpie`` 实例，一个为自动处理的option。

看起来像这样：

.. code:: python

    {'-h': <function docpie.Docpie.help_handler>,
     '--help': <function docpie.Docpie.help_handler>,
     '-v': <function docpie.Docpie.version_handler>,
     '--version': <function docpie.Docpie.version_handler>,
    }

当设定 ``version`` 不为 ``None`` 时，Docpie会按如下步骤操作（ ``pie`` 为 ``Docpie`` 实例）：

1. 设置 ``pie.version`` 属性
2. 检查"--version"是否在"Options"中定义
3. 如果定义了，设置"--version"和同名option为键， ``Docpie.version_handler`` 为值
   到 ``pie.extra`` 中。
4. 如果未定义，换而检查"-v"
5. 如果"-v"和"--version"都在"Options"中未定义，则直接使用"-v"和"--version"作为键。
6. 调用 ``pie.docpie`` 时，检查 ``pie.extra`` 的键是否出现在 ``argv`` 中。
7. 如果出现，例如 ``-v`` ，则调用 ``pie.extra["-v"](pie, "-v")``
8. 默认 ``Docpie.version_handler(docpie, flag)`` 将打印
   ``pie.version`` 并退出程序。

对于 ``help=True`` ， ``Docpie``  则检查"--help"和"-h"，然后设置值为
``Docpie.help_handler`` 。

两种自定义的方法：

extra参数
^^^^^^^^^^^^^^

你可以穿入 ``extra`` 参数，例如：

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

现在试试：

.. code:: bash

    example.py -v
    example.py --version
    example.py -h
    example.py -?
    example.py --help
    example.py --moo

``option_sections`` 是个啥？请移步"Docpie属性"章节

set_auto_handler
^^^^^^^^^^^^^^^^

.. code:: python

    Docpie.set_auto_handler(self, flag, handler)

当设制 ``extra`` 参数时， ``Docpie`` 并不会检查你定义的同名option。
而 ``set_auto_handler`` 可以让所有同名option添加相同行为。

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

这样的话 ``Docpie`` 会同时自动处理 ``-m`` 和 ``--moo`` 。


Docpie属性
~~~~~~~~~~~~~~~~

为自定义 ``extra`` ，这些 ``Docpie`` 属性可能会有用：

-  ``pie.version`` 为你设定的version(默认 ``None`` )
-  ``pie.usage_text`` 为你定义的“Usage”区域
-  ``pie.option_sections`` 为一个 ``dict`` ，包含了你定义的所有 ``Options`` 章节。
   键为你"Options:"前面的字符：

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


序列化
~~~~~~~~~~~~~

（pie为Docpie实例）

``pie.convert_2_dict()`` 可以将 ``Docpie`` 实例转为一个字典，然后你就可以保存为JSON格式了。
用 ``Docpie.convert_2_docpie(dic)`` 来把这个字典回转为实例。

**注意：** 如果你传递了 ``extra`` 参数或调用过 ``set_auto_handler`` 方法，
这部分信息会丢失，因为JSON无法保存一个可回调对象。
你需要在反序列化后使用 ``set_config(extra={...})`` 或者 ``set_auto_handler`` 。

这里是搭配 `pickle <https://docs.python.org/3/library/pickle.html>`__ 的完整示例。

开发：

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

发布：

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

预览
~~~~~~~

对实例 ``pie=Docpie(__doc__)`` ，调用 ``pie.preview()`` 来查看 ``Docpie`` 是如何解析
你的帮助信息的。

`注意` 这跟你定义的格式并不完全相同。

区别于docopt
-------------

``docpie`` 不是 ``docopt`` 。

1. ``docpie`` 使用 ``Options:`` 来查找对应的"Option"章节，而 ``docopt``
   则将所有 ``-`` 开头（忽略开头的空白）的行视为Options"。

2. ``auto2dashes=True`` 时 ``docpie`` 会自动处理并添加 ``--`` 到结果。
   ``docpie`` 还会将同名option添加到结果。

已知问题
------------

``docpie`` 支持在重复参数后面继续定义参数（注意参数匹配总是贪婪的），但这个支持较有限。

::

    Usage: cp.py <source_file>... <target_directory> [-f] [-r]

1. 重复元素必须且只能为 ``ARGUMENT``：

   -  可行:  ``(<arg1>)... <arg2> <arg3>``
   -  可行:  ``[<arg1>]... <arg2>``
   -  不行:  ``(<arg1> <arg2>)... <arg3>``
   -  不行:  ``-a... -a``
   -  不行:  ``cmd... cmd``

2. 后续元素必须为 ``ARGUMENT`` 且不能用 ``()`` ,  ``[]`` 分组

   -  ``<arg1>... <arg1> <arg2> command`` : 无法匹配
      ``val1 val2 val3 command``
   -  ``<arg1>... (<arg2>)`` 无法匹配任何argv

开发
-----------

执行 ``/test.py`` 来运行测试

``docpie`` 的logger名为 ``"docpie"``

``docpie`` 含两个调试工具： ``bashlog`` 和 ``tracemore`` 。基本用法为：

.. code:: python

    from docpie import docpie, bashlog
    from docpie.tracemore import get_exc_plus

    logger = bashlog.stdoutlogger('docpie')  # You may init your logger in your way

    try:
        docpie(doc)
    except BaseException:
        logger.error(get_exc_plus())

``bashlog.py`` 代码来自
`tornado <https://github.com/tornadoweb/tornado>`__，
``tracemore.py`` 来自 `python
Cookbook <http://www.amazon.com/Python-Cookbook-Third-David-Beazley/dp/1449340377/ref=sr_1_1?ie=UTF8&qid=1440593849&sr=8-1&keywords=python+cookbook>`__

许可协议
---------

``docpie`` 基于
`MIT-License <https://github.com/TylerTemp/docpie/blob/master/LICENSE>`__
发布
