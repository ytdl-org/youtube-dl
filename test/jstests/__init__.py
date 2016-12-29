"""
This package contains templates for `test_jsinterp` and `test_interp_parse` to create test methods.
These modules will create a test method for each module in this package. A test method consist of one or more subtest.
Each subtest initializes an instance of the tested class and runs one or more assertion.

Any module should have a `list` of `dict` named ``tests`` and optionally a `dict` named ``skip``.

Each `dict` in ``tests`` may have the following keys:

    code: If missing subtest is skipped, Otherwise it's value is used as code to initialize the tested class.
    globals: Optional. Used only by `test_jsinterp`. If set used as argument `variables` initializing `JSInterperter`.
    asserts: Used only by `test_jsinterp`. If this is missing subtest is skipped, Should be a list of `dict`, each used
             as an assertion for the initialized `JSInterpreter`. Each `dict` may have the following keys:
                value: If missing assertion is skipped. Otherwise it's value is used as expected value in
                       an `assertEqual` call.
                call: Optional. If set used as arguments of a `call_function` call of the initialized `JSInterpreter`
                      and the actual value of the created `assertEqual` call will be the return value of it.
                      Otherwise the actual value will be the return value of the `run` call.
    ast: Used only by `test_interp_parse`. If missing subtest is skipped, Otherwise it's value is used as
         expected value in an `assertEqual` call. The actual value will be the return value of the `parse` call
         converted to `list`. Both on expected anc actual value `traverse` is called first to flatten and handle `zip`
         objects.

In the `dict` named ``skip`` is optional and may have the following keys:
    interpret
    parse
Both used as the argument of `skipTest` decorator of the created test method in `test_jsinterp`
and `test_jsinterp_parse` respectably. Unless they're value is `True`, that case the test method is skipped entirely,
or `False`, which is the default value.

Example:
    This is not a functional template, rather a skeleton:

        skip = {'interpret': 'Test not yet implemented',
                'parse': 'Test not yet implemented'}

        tests = [
            {
                'code': '',
                'globals': {},
                'asserts': [{'value': 0, 'call': ('f',)}],
                'ast': []
            }
        ]
"""


def gettestcases():
    import os

    modules = [module[:-3] for module in os.listdir(os.path.dirname(__file__))
               if module != '__init__.py' and module[-3:] == '.py']
    me = __import__(__name__, globals(), locals(), modules)

    for module_name in modules:
        module = getattr(me, module_name)
        if hasattr(module, 'tests'):
            case = {
                'name': module.__name__[len(__name__) + 1:],
                'subtests': module.tests,
                'skip': getattr(module, 'skip', {})
            }
            yield case
