from . import (
    array_access,
    assignments,
    basic,
    branch,
    calc,
    call,
    comments,
    debug,
    do_loop,
    empty_return,
    for_empty,
    for_in,
    for_loop,
    func_expr,
    getfield,
    label,
    morespace,
    object_literal,
    operators,
    parens,
    precedence,
    strange_chars,
    switch,
    try_statement,
    unary,
    unshift,
    while_loop,
    with_statement
)


modules = [array_access, assignments, basic, branch, calc, call, comments, debug, do_loop, empty_return, for_empty,
           for_in, for_loop, func_expr, getfield, label, morespace, object_literal, operators, parens, precedence,
           strange_chars, switch, try_statement, unary, unshift, while_loop, with_statement]


def gettestcases():
    for module in modules:
        if hasattr(module, 'tests'):
            case = {'name': module.__name__[len(__name__) + 1:], 'subtests': [], 'skip': {}}
            for test in getattr(module, 'tests'):
                if 'code' in test:
                    case['subtests'].append(test)
            if hasattr(module, 'skip'):
                case['skip'] = getattr(module, 'skip')
            yield case
