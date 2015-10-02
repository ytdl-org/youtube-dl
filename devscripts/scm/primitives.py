from __future__ import unicode_literals

import re
import sys


"""
Module implemeting a minimal subset of Scheme primitives in term of Python

In Scheme:
    apply car cdr cons display even? length list list->lst lst->list lst->tuple
    list? null? object->string odd? pair? string? string->symbol symbol->string
    symbol? tuple->lst

In Python:
    apply car cdr cons display is_even length list list_to_lst lst_to_list
    lst_to_tuple is_list is_null object_to_string is_odd is_pair is_string
    string_to_symbol symbol_to_string is_symbol tuple_to_lst

"""

# standalone primitives

if sys.version_info < (3, 0):
    def display(obj): print(obj.encode("utf-8"))
else:
    def display(obj): print(obj)

def is_even(x): return x % 2 == 0

def is_odd(x): return x % 2 != 0

if sys.version_info < (3, 0):
    is_string = lambda obj: isinstance(obj, (str, basestring))
else:
    is_string = lambda obj: isinstance(obj, str)

if sys.version_info < (3, 0):
    object_to_string = lambda obj: unicode(obj)
else:
    object_to_string = lambda obj: str(obj)

# nil-related primitives

class _Nil:
    """internal class implementing the empty lst type"""
    def __repr__(self): return "()"

    def __str__(self): return "()"

# Many Scheme implementations don't have nil and use '() instead,
# but we can't do that as we don't know how to get quoting works in Python...
nil = _Nil()

def is_null(x): return x is nil


# pair/lst-related primitives

class _Pair:
    """internal class implementing the pair type"""
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
        if cdr is nil or is_list(cdr):
            self.is_list = True
        else:
            self.is_list = False

    def __repr__(self):
        """
        Simulate representation of pair and list in Scheme REPL

        In general, cons(x, y) is called a pair and is represented by (x . y)

        However, if y is the empty lst, then cons(x, y) is called a lst
        (avoid confusing with the procedure list,
        treat list as a verb and lst as a noun)
        and is represented by (x)

        Moroever, if y is a lst and represented by (foo),
        then cons(x,y) is also a lst and is represented by (x foo)

        """
        pattern = r"^\(|\)$"
        if self.cdr is nil:
            return "(" + repr(self.car) + ")"
        elif self.is_list:
            return "(" + repr(self.car) + " " + \
                re.sub(pattern, "", repr(self.cdr)) + ")"
        else:
            return "(" + repr(self.car) + " . " + repr(self.cdr) + ")"

    def __str__(self):
        """
        Same as __repr__.

        Except repr(self.car) and repr(self.cdr) are replaced by
        object_to_string(self.car) and object_to_string(self.cdr) respectively.

        """
        pattern = r"^\(|\)$"
        if self.is_list:
            return "(" + object_to_string(self.car) + " " + \
                re.sub(pattern, "", object_to_string(self.cdr)) + ")"
        else:
            return "(" + object_to_string(self.car) + " . " + \
                object_to_string(self.cdr) + ")"

    def __eq__(self, x):
        return isinstance(x, _Pair) and self.car == x.car and self.cdr == x.cdr

def cons(a, b): return _Pair(a, b)

def car(pair): return pair.car

def cdr(pair): return pair.cdr

def is_pair(x): return isinstance(x, _Pair)

def is_list(x):
    if x is nil:
        return True
    elif isinstance(x, _Pair):
        return x.is_list
    else:
        return False

def list(*arg_tup):
    """build a lst from any number of elements"""
    if arg_tup is ():
        return nil
    else:
        return cons(arg_tup[0], list(*arg_tup[1:]))

def tuple_to_lst(tup):
    """convert Python tuple to Scheme lst"""
    if not tup:
        return nil
    else:
        return cons(tup[0], tuple_to_lst(tup[1:]))

def lst_to_tuple(lst):
    """convert Scheme lst to Python tuple"""
    if lst is nil:
        return ()
    else:
        return (lst.car,) + lst_to_tuple(lst.cdr)

def apply(proc, lst):
    """apply procedure proc to a Scheme lst"""
    return proc(*lst_to_tuple(lst))

def list_to_lst(list_):
    """convert Python list to Scheme lst"""
    if not list_:
        return nil
    else:
        return cons(list_[0], list_to_lst(list_[1:]))

def lst_to_list(lst):
    """convert Scheme lst to Python list"""
    if lst is nil:
        return []
    else:
        return [lst.car,] + lst_to_list(lst.cdr)


# symbol-related primitives

# maintain a dictionary of symbol, to avoid duplication of _Symbol object
_symbol_dict = {}

class _Symbol:
    """internal class implementing the symbol type"""
    def __init__(self, string):
        self.string = string
        _symbol_dict[string] = self

    def __repr__(self):
        """remove leading and trailing quote from repr(self.string)"""
        pattern = r"^'|^\"|\"$|'$"
        return re.sub(pattern, "", repr(self.string))

    def __str__(self):
        return object_to_string(self.string)

def string_to_symbol(string):
    """convert Python string to Scheme symbol"""
    if string not in _symbol_dict:
        _symbol_dict[string] = _Symbol(string)
    return _symbol_dict[string]

def symbol_to_string(symbol): return object_to_string(symbol)

def is_symbol(x): return isinstance(_Symbol)
