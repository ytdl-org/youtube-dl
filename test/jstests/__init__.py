from . import (
    basic,
    calc,
    empty_return,
    morespace,
    strange_chars,
    operators,
    array_access,
    parens,
    assignments,
    comments,
    precedence,
    call,
    getfield,
    branch,
    switch,
    for_loop,
    for_empty,
    for_in,
    do_loop,
    while_loop,
    label,
    func_expr,
    object_literal,
    try_statement,
    with_statement,
    debug,
    unshift
)


modules = [basic, calc, empty_return, morespace, strange_chars, operators, array_access, parens, assignments, comments,
           precedence, call, getfield, branch, switch, for_loop, for_empty, for_in, do_loop, while_loop, label,
           func_expr, object_literal, try_statement, with_statement, debug, unshift]


def gettestcases():
    for module in modules:
        if hasattr(module, 'tests'):
            case = {'name': module.__name__[len(__name__) + 1:], 'subtests': []}
            for test in getattr(module, 'tests'):
                if 'code' in test:
                    case['subtests'].append(test)
            if hasattr(module, 'skip'):
                case['skip'] = getattr(module, 'skip')
            yield case
