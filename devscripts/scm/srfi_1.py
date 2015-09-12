from __future__ import unicode_literals

from .primitives import *


"""
Module implemeting a minimal subset of SRFI-1: List Library

In Scheme:
    append caar cadr cdar cddr caaar caadr cadar caddr cdaar cdadr cddar cdddr
    caaaar caaadr caadar caaddr cadaar cadadr caddar cadddr cdaaar cdaadr
    cdadar cdaddr cddaar cddadr cdddar cddddr concatenate drop-while every
    filter first fold iota last length list list_ref lset-difference map reduce
    reverse take-while

In Python:
    append caar cadr cdar cddr caaar caadr cadar caddr cdaar cdadr cddar cdddr
    caaaar caaadr caadar caaddr cadaar cadadr caddar cadddr cdaaar cdaadr
    cdadar cdaddr cddaar cddadr cdddar cddddr concatenate drop_while every
    filter first fold iota last length list list_ref lset_difference map reduce
    reverse take_while

"""

# Use these procedures with caution,
# as too much car/cdr-ing may hinder readability

def caar(obj): return car(car(obj))

def cadr(obj): return car(cdr(obj))

def cdar(obj): return cdr(car(obj))

def cddr(obj): return cdr(cdr(obj))

def caaar(obj): return car(car(car(obj)))

def caadr(obj): return car(car(cdr(obj)))

def cadar(obj): return car(cdr(car(obj)))

def caddr(obj): return car(cdr(cdr(obj)))

def cdaar(obj): return cdr(car(car(obj)))

def cdadr(obj): return cdr(car(cdr(obj)))

def cddar(obj): return cdr(cdr(car(obj)))

def cdddr(obj): return cdr(cdr(cdr(obj)))

def caaaar(obj): return car(car(car(car(obj))))

def caaadr(obj): return car(car(car(cdr(obj))))

def caadar(obj): return car(car(cdr(car(obj))))

def caaddr(obj): return car(car(cdr(cdr(obj))))

def cadaar(obj): return car(cdr(car(car(obj))))

def cadadr(obj): return car(cdr(car(cdr(obj))))

def caddar(obj): return car(cdr(cdr(car(obj))))

def cadddr(obj): return car(cdr(cdr(cdr(obj))))

def cdaaar(obj): return cdr(car(car(car(obj))))

def cdaadr(obj): return cdr(car(car(cdr(obj))))

def cdadar(obj): return cdr(car(cdr(car(obj))))

def cdaddr(obj): return cdr(car(cdr(cdr(obj))))

def cddaar(obj): return cdr(cdr(car(car(obj))))

def cddadr(obj): return cdr(cdr(car(cdr(obj))))

def cdddar(obj): return cdr(cdr(cdr(car(obj))))

def cddddr(obj): return cdr(cdr(cdr(cdr(obj))))

def length(lst):
    """compute length of lst"""
    def length_loop(lst, count):
        if lst is nil:
            return count
        else:
            return length_loop(cdr(lst),
                               count + 1)
    return length_loop(lst, 0)

def list_ref(lst, k):
    """return the k^th element of lst"""
    if k == 0:
        return car(lst)
    else:
        return list_ref(cdr(lst), k - 1)

def iota(count):
    """return lst from 0 to (count - 1)"""
    def iota_loop(loop_count):
        if loop_count == count:
            return nil
        else:
            return cons(loop_count,
                        iota_loop(loop_count + 1))
    return iota_loop(0)

def _any(proc, arg_lst):
    """
    any for procedures that take a single argument

    Apply proc to every element in arg_lst
    Return True is any of the result is True
    Otherwise, return False

    """
    if arg_lst is nil:
        return False
    elif proc(car(arg_lst)):
        return True
    else:
        return _any(proc, cdr(arg_lst))

def _every(proc, arg_lst):
    """
    every for procedures that take a single argument

    Apply proc to every element in arg_lst
    Return True is every result is True
    Otherwise, return False

    """
    if arg_lst is nil:
        return True
    elif not proc(car(arg_lst)):
        return False
    else:
        return _every(proc, cdr(arg_lst))

def _map(proc, lst):
    """
    map for procedures that take a single argument

    Apply proc to every element in arg_lst and return the resulting lst

    """
    if lst is nil:
        return nil
    else:
        return cons(proc(car(lst)),
                    _map(proc, cdr(lst)))

def map(proc, *tuple_of_lst):
    """
    map for procedures that take any number of arguments, including 1

    Apply proc to the n^th element in lst from lst_of_lst
    and return the resulting lst

    """
    lst_of_lst = tuple_to_lst(tuple_of_lst)
    if _every(is_null, lst_of_lst):
        return nil
    elif _any(is_null, lst_of_lst):
        raise IndexError("some of the lists are differed in length!")
    else:
        return cons(apply(proc,
                          _map(car, lst_of_lst)),
                    apply(map, cons(proc,
                                    _map(cdr, lst_of_lst))))

def _fold(proc, init, lst):
    """
    fold for procedures that take a single argument

    If lst is the empty lst, return init
    Otherwise, apply proc to the first element of lst and init in this order
    Now, the result becomes the new init

    """

    if lst is nil:
        return init
    else:
        return _fold(proc, proc(car(lst), init), cdr(lst))

def reduce(proc, default, lst):
    """
    If lst is the empty lst, return default
    Otherwise, apply proc to the second element in lst
    and the first element from lst in this order
    Now, the result becomes the element after the remaining first element

    """
    if lst is nil:
        return default
    elif cdr(lst) is nil:
        return car(lst)
    else:
        return _fold(proc, car(lst), cdr(lst))

def any(proc, *tuple_of_lst):
    """
    any for procedures that take any number of arguments, including 1

    Apply proc to the n^th element in lst from lst_of_lst
    Return True is any of the result is True
    Otherwise, return False

    """
    lst_of_lst = tuple_to_lst(tuple_of_lst)
    return reduce(lambda x, y: x or y,
                  False,
                  apply(_map, cons(proc,
                                   lst_of_lst)))

def every(proc, *tuple_of_lst):
    """
    every for procedures that take any number of arguments, including 1

    Apply proc to the n^th element in lst from lst_of_lst
    Return True is any of the result is True
    Otherwise, return False

    """
    lst_of_lst = tuple_to_lst(tuple_of_lst)
    return reduce(lambda x, y: x and y,
                  True,
                  apply(_map, cons(proc,
                                   lst_of_lst)))

def reverse(lst):
    """reverse a given lst"""
    return _fold(cons, nil, lst)

def filter(proc, lst):
    """
    Apply proc to elements in lst
    Remove those evaluated to False and return the resulting lst

    """
    def filter_loop(proc, lst, accum):
        if lst is nil:
            return accum
        elif proc(car(lst)):
            return filter_loop(proc, cdr(lst), cons(car(lst), accum))
        else:
            return filter_loop(proc,
                               cdr(lst),
                               accum)
    return reverse(filter_loop(proc, lst, nil))

def first(lst):
    """return the first element of lst, usually used with last"""
    return car(lst)

def last(lst):
    """return the last element of lst, usually used with first"""
    return car(reverse(lst))

def _append(lst1, lst2):
    """
    append for procedure that takes a single argument

    Append 2 lst into a single lst

    """

    return _fold(cons, lst2, reverse(lst1))

def append(*tuple_of_lst):
    """
    append for procedures that take any number of arguments, including 1

    Append any number of lst into a single lst

    """

    lst_of_lst = tuple_to_lst(tuple_of_lst)
    return reduce(_append, nil, reverse(lst_of_lst))

def concatenate(lst_of_lst):
    """concatenate lst_of_lst into a single lst"""
    return apply(append, lst_of_lst)

def fold(proc, init, *tuple_of_lst):
    """
    fold for procedures that take any number of arguments, including 1

    If every element in lst_of_lst is the empty lst, return init
    Otherwise, apply proc to the first element of every element in lst_of_lst
    and init in this order
    Now, the result becomes the new init

    """

    lst_of_lst = tuple_to_lst(tuple_of_lst)
    if _every(is_null, lst_of_lst):
        return init
    elif _any(is_null, lst_of_lst):
        raise IndexError("some of the lists are differed in length!")
    else:
        return apply(fold, cons(proc,
                                cons(apply(proc,
                                           append(_map(car, lst_of_lst),
                                                  list(init))),
                                     _map(cdr, lst_of_lst))))

def lset_difference(comparator, lst, *tuple_of_lst):
    def _lset_difference(comparator, lst1, lst2):
        """treat lst1 and lst2 as sets and compute lst1 \ lst2"""
        return filter(lambda x: _every(lambda y: not comparator(x, y),
                                       lst2),
                      lst1)
    lst_of_lst = tuple_to_lst(tuple_of_lst)
    if lst_of_lst is nil:
        return lst
    else:
        return apply(lset_difference,
                     cons(comparator,
                          cons(_lset_difference(comparator,
                                                lst,
                                                car(lst_of_lst)),
                               cdr(lst_of_lst))))

def drop_while(pred, lst):
    """
    While predicate evaluates to True, drops the element

    Return the lst if predicate evaluates to False or if lst is empty

    """
    if lst is nil:
        return nil
    elif not pred(car(lst)):
        return lst
    else:
        return drop_while(pred, cdr(lst))

def take_while(pred, lst):
    """
    While predicate evaluates to True, takes the element

    Return the empty lst if predicate evaluates to False or if lst is empty

    """
    if lst is nil:
        return nil
    elif not pred(car(lst)):
        return nil
    else:
        return cons(car(lst), take_while(pred, cdr(lst)))
