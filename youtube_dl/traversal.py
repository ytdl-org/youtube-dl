# coding: utf-8

import itertools
import inspect

from .compat import (
    compat_casefold,
    compat_etree_iterfind,
    compat_re_Match,
    compat_str,
    compat_contextlib_suppress,
    compat_http_cookies,
    compat_collections_abc,
    compat_etree_Element,

)

NO_DEFAULT = object()
IDENTITY = lambda x: x


class LazyList(compat_collections_abc.Iterable):
    """Lazy immutable list from an iterable
    Note that slices of a LazyList are lists and not LazyList"""

    class IndexError(IndexError):
        def __init__(self, cause=None):
            if cause:
                # reproduce `raise from`
                self.__cause__ = cause
            super(IndexError, self).__init__()

    def __init__(self, iterable, **kwargs):
        # kwarg-only
        reverse = kwargs.get('reverse', False)
        _cache = kwargs.get('_cache')

        self._iterable = iter(iterable)
        self._cache = [] if _cache is None else _cache
        self._reversed = reverse

    def __iter__(self):
        if self._reversed:
            # We need to consume the entire iterable to iterate in reverse
            for item in self.exhaust():
                yield item
            return
        for item in self._cache:
            yield item
        for item in self._iterable:
            self._cache.append(item)
            yield item

    def _exhaust(self):
        self._cache.extend(self._iterable)
        self._iterable = []  # Discard the emptied iterable to make it pickle-able
        return self._cache

    def exhaust(self):
        """Evaluate the entire iterable"""
        return self._exhaust()[::-1 if self._reversed else 1]

    @staticmethod
    def _reverse_index(x):
        return None if x is None else ~x

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if self._reversed:
                idx = slice(self._reverse_index(idx.start), self._reverse_index(idx.stop), -(idx.step or 1))
            start, stop, step = idx.start, idx.stop, idx.step or 1
        elif isinstance(idx, int):
            if self._reversed:
                idx = self._reverse_index(idx)
            start, stop, step = idx, idx, 0
        else:
            raise TypeError('indices must be integers or slices')
        if ((start or 0) < 0 or (stop or 0) < 0
                or (start is None and step < 0)
                or (stop is None and step > 0)):
            # We need to consume the entire iterable to be able to slice from the end
            # Obviously, never use this with infinite iterables
            self._exhaust()
            try:
                return self._cache[idx]
            except IndexError as e:
                raise self.IndexError(e)
        n = max(start or 0, stop or 0) - len(self._cache) + 1
        if n > 0:
            self._cache.extend(itertools.islice(self._iterable, n))
        try:
            return self._cache[idx]
        except IndexError as e:
            raise self.IndexError(e)

    def __bool__(self):
        try:
            self[-1] if self._reversed else self[0]
        except self.IndexError:
            return False
        return True

    def __len__(self):
        self._exhaust()
        return len(self._cache)

    def __reversed__(self):
        return type(self)(self._iterable, reverse=not self._reversed, _cache=self._cache)

    def __copy__(self):
        return type(self)(self._iterable, reverse=self._reversed, _cache=self._cache)

    def __repr__(self):
        # repr and str should mimic a list. So we exhaust the iterable
        return repr(self.exhaust())

    def __str__(self):
        return repr(self.exhaust())


def is_iterable_like(x, allowed_types=compat_collections_abc.Iterable, blocked_types=NO_DEFAULT):
    if blocked_types is NO_DEFAULT:
        blocked_types = (compat_str, bytes, compat_collections_abc.Mapping)
    return isinstance(x, allowed_types) and not isinstance(x, blocked_types)


def variadic(x, allowed_types=NO_DEFAULT):
    if isinstance(allowed_types, compat_collections_abc.Iterable):
        allowed_types = tuple(allowed_types)
    return x if is_iterable_like(x, blocked_types=allowed_types) else (x,)


def try_call(*funcs, **kwargs):

    # parameter defaults
    expected_type = kwargs.get('expected_type')
    fargs = kwargs.get('args', [])
    fkwargs = kwargs.get('kwargs', {})

    for f in funcs:
        try:
            val = f(*fargs, **fkwargs)
        except (AttributeError, KeyError, TypeError, IndexError, ZeroDivisionError):
            pass
        else:
            if expected_type is None or isinstance(val, expected_type):
                return val


if __debug__:
    # Raise TypeError if args can't be bound
    # needs compat owing to unstable inspect API, thanks PSF :-(
    try:
        inspect.signature

        def _try_bind_args(fn, *args, **kwargs):
            inspect.signature(fn).bind(*args, **kwargs)
    except AttributeError:
        # Py < 3.3
        def _try_bind_args(fn, *args, **kwargs):
            fn_args = inspect.getargspec(fn)
            # Py2: ArgInfo(args, varargs, keywords, defaults)
            # Py3: ArgSpec(args, varargs, keywords, defaults)
            if not fn_args.keywords:
                for k in kwargs:
                    if k not in (fn_args.args or []):
                        raise TypeError("got an unexpected keyword argument: '{0}'".format(k))
            if not fn_args.varargs:
                args_to_bind = len(args)
                bindable = len(fn_args.args or [])
                if args_to_bind > bindable:
                    raise TypeError('too many positional arguments')
                bindable -= len(fn_args.defaults or [])
                if args_to_bind < bindable:
                    if kwargs:
                        bindable -= len(set(fn_args.args or []) & set(kwargs))
                    if bindable > args_to_bind:
                        raise TypeError("missing a required argument: '{0}'".format(fn_args.args[args_to_bind]))


def traverse_obj(obj, *paths, **kwargs):
    """
    Safely traverse nested `dict`s and `Iterable`s, etc

    >>> obj = [{}, {"key": "value"}]
    >>> traverse_obj(obj, (1, "key"))
    'value'

    Each of the provided `paths` is tested and the first producing a valid result will be returned.
    The next path will also be tested if the path branched but no results could be found.
    Supported values for traversal are `Mapping`, `Iterable`, `re.Match`, `xml.etree.ElementTree`
    (xpath) and `http.cookies.Morsel`.
    Unhelpful values (`{}`, `None`) are treated as the absence of a value and discarded.

    The paths will be wrapped in `variadic`, so that `'key'` is conveniently the same as `('key', )`.

    The keys in the path can be one of:
        - `None`:           Return the current object.
        - `set`:            Requires the only item in the set to be a type or function,
                            like `{type}`/`{type, type, ...}`/`{func}`. If one or more `type`s,
                            return only values that have one of the types. If a function,
                            return `func(obj)`.
        - `str`/`int`:      Return `obj[key]`. For `re.Match`, return `obj.group(key)`.
        - `slice`:          Branch out and return all values in `obj[key]`.
        - `Ellipsis`:       Branch out and return a list of all values.
        - `tuple`/`list`:   Branch out and return a list of all matching values.
                            Read as: `[traverse_obj(obj, branch) for branch in branches]`.
        - `function`:       Branch out and return values filtered by the function.
                            Read as: `[value for key, value in obj if function(key, value)]`.
                            For `Sequence`s, `key` is the index of the value.
                            For `Iterable`s, `key` is the enumeration count of the value.
                            For `re.Match`es, `key` is the group number (0 = full match)
                            as well as additionally any group names, if given.
        - `dict`:           Transform the current object and return a matching dict.
                            Read as: `{key: traverse_obj(obj, path) for key, path in dct.items()}`.
        - `any`-builtin:    Take the first matching object and return it, resetting branching.
        - `all`-builtin:    Take all matching objects and return them as a list, resetting branching.

        `tuple`, `list`, and `dict` all support nested paths and branches.

    @params paths           Paths which to traverse by.
    Keyword arguments:
    @param default          Value to return if the paths do not match.
                            If the last key in the path is a `dict`, it will apply to each value inside
                            the dict instead, depth first. Try to avoid if using nested `dict` keys.
    @param expected_type    If a `type`, only accept final values of this type.
                            If any other callable, try to call the function on each result.
                            If the last key in the path is a `dict`, it will apply to each value inside
                            the dict instead, recursively. This does respect branching paths.
    @param get_all          If `False`, return the first matching result, otherwise all matching ones.
    @param casesense        If `False`, consider string dictionary keys as case insensitive.

    The following is only meant to be used by YoutubeDL.prepare_outtmpl and is not part of the API

    @param _traverse_string  Whether to traverse into objects as strings.
                            If `True`, any non-compatible object will first be
                            converted into a string and then traversed into.
                            The return value of that path will be a string instead,
                            not respecting any further branching.


    @returns                The result of the object traversal.
                            If successful, `get_all=True`, and the path branches at least once,
                            then a list of results is returned instead.
                            A list is always returned if the last path branches and no `default` is given.
                            If a path ends on a `dict` that result will always be a `dict`.
    """

    # parameter defaults
    default = kwargs.get('default', NO_DEFAULT)
    expected_type = kwargs.get('expected_type')
    get_all = kwargs.get('get_all', True)
    casesense = kwargs.get('casesense', True)
    _traverse_string = kwargs.get('_traverse_string', False)

    # instant compat
    str = compat_str

    casefold = lambda k: compat_casefold(k) if isinstance(k, str) else k

    if isinstance(expected_type, type):
        type_test = lambda val: val if isinstance(val, expected_type) else None
    else:
        type_test = lambda val: try_call(expected_type or IDENTITY, args=(val,))

    def lookup_or_none(v, k, getter=None):
        with compat_contextlib_suppress(LookupError):
            return getter(v, k) if getter else v[k]

    def from_iterable(iterables):
        # chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
        for it in iterables:
            for item in it:
                yield item

    def apply_key(key, obj, is_last):
        branching = False

        if obj is None and _traverse_string:
            if key is Ellipsis or callable(key) or isinstance(key, slice):
                branching = True
                result = ()
            else:
                result = None

        elif key is None:
            result = obj

        elif isinstance(key, set):
            assert len(key) >= 1, 'At least one item is required in a `set` key'
            if all(isinstance(item, type) for item in key):
                result = obj if isinstance(obj, tuple(key)) else None
            else:
                item = next(iter(key))
                assert len(key) == 1, 'Multiple items in a `set` key must all be types'
                result = try_call(item, args=(obj,)) if not isinstance(item, type) else None

        elif isinstance(key, (list, tuple)):
            branching = True
            result = from_iterable(
                apply_path(obj, branch, is_last)[0] for branch in key)

        elif key is Ellipsis:
            branching = True
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, compat_collections_abc.Mapping):
                result = obj.values()
            elif is_iterable_like(obj, (compat_collections_abc.Iterable, compat_etree_Element)):
                result = obj
            elif isinstance(obj, compat_re_Match):
                result = obj.groups()
            elif _traverse_string:
                branching = False
                result = str(obj)
            else:
                result = ()

        elif callable(key):
            branching = True
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, compat_collections_abc.Mapping):
                iter_obj = obj.items()
            elif is_iterable_like(obj, (compat_collections_abc.Iterable, compat_etree_Element)):
                iter_obj = enumerate(obj)
            elif isinstance(obj, compat_re_Match):
                iter_obj = itertools.chain(
                    enumerate(itertools.chain((obj.group(),), obj.groups())),
                    obj.groupdict().items())
            elif _traverse_string:
                branching = False
                iter_obj = enumerate(str(obj))
            else:
                iter_obj = ()

            result = (v for k, v in iter_obj if try_call(key, args=(k, v)))
            if not branching:  # string traversal
                result = ''.join(result)

        elif isinstance(key, dict):
            iter_obj = ((k, _traverse_obj(obj, v, False, is_last)) for k, v in key.items())
            result = dict((k, v if v is not None else default) for k, v in iter_obj
                          if v is not None or default is not NO_DEFAULT) or None

        elif isinstance(obj, compat_collections_abc.Mapping):
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            result = (try_call(obj.get, args=(key,))
                      if casesense or try_call(obj.__contains__, args=(key,))
                      else next((v for k, v in obj.items() if casefold(k) == key), None))

        elif isinstance(obj, compat_re_Match):
            result = None
            if isinstance(key, int) or casesense:
                # Py 2.6 doesn't have methods in the Match class/type
                result = lookup_or_none(obj, key, getter=lambda _, k: obj.group(k))

            elif isinstance(key, str):
                result = next((v for k, v in obj.groupdict().items()
                              if casefold(k) == key), None)

        else:
            result = None
            if isinstance(key, (int, slice)):
                if is_iterable_like(obj, (compat_collections_abc.Sequence, compat_etree_Element)):
                    branching = isinstance(key, slice)
                    result = lookup_or_none(obj, key)
                elif _traverse_string:
                    result = lookup_or_none(str(obj), key)

            elif isinstance(obj, compat_etree_Element) and isinstance(key, str):
                xpath, _, special = key.rpartition('/')
                if not special.startswith('@') and not special.endswith('()'):
                    xpath = key
                    special = None

                # Allow abbreviations of relative paths, absolute paths error
                if xpath.startswith('/'):
                    xpath = '.' + xpath
                elif xpath and not xpath.startswith('./'):
                    xpath = './' + xpath

                def apply_specials(element):
                    if special is None:
                        return element
                    if special == '@':
                        return element.attrib
                    if special.startswith('@'):
                        return try_call(element.attrib.get, args=(special[1:],))
                    if special == 'text()':
                        return element.text
                    raise SyntaxError('apply_specials is missing case for {0!r}'.format(special))

                if xpath:
                    result = list(map(apply_specials, compat_etree_iterfind(obj, xpath)))
                else:
                    result = apply_specials(obj)

        return branching, result if branching else (result,)

    def lazy_last(iterable):
        iterator = iter(iterable)
        prev = next(iterator, NO_DEFAULT)
        if prev is NO_DEFAULT:
            return

        for item in iterator:
            yield False, prev
            prev = item

        yield True, prev

    def apply_path(start_obj, path, test_type):
        objs = (start_obj,)
        has_branched = False

        key = None
        for last, key in lazy_last(variadic(path, (str, bytes, dict, set))):
            if not casesense and isinstance(key, str):
                key = compat_casefold(key)

            if key in (any, all):
                has_branched = False
                filtered_objs = (obj for obj in objs if obj not in (None, {}))
                if key is any:
                    objs = (next(filtered_objs, None),)
                else:
                    objs = (list(filtered_objs),)
                continue

            if __debug__ and callable(key):
                # Verify function signature
                _try_bind_args(key, None, None)

            new_objs = []
            for obj in objs:
                branching, results = apply_key(key, obj, last)
                has_branched |= branching
                new_objs.append(results)

            objs = from_iterable(new_objs)

        if test_type and not isinstance(key, (dict, list, tuple)):
            objs = map(type_test, objs)

        return objs, has_branched, isinstance(key, dict)

    def _traverse_obj(obj, path, allow_empty, test_type):
        results, has_branched, is_dict = apply_path(obj, path, test_type)
        results = LazyList(x for x in results if x not in (None, {}))

        if get_all and has_branched:
            if results:
                return results.exhaust()
            if allow_empty:
                return [] if default is NO_DEFAULT else default
            return None

        return results[0] if results else {} if allow_empty and is_dict else None

    for index, path in enumerate(paths, 1):
        result = _traverse_obj(obj, path, index == len(paths), True)
        if result is not None:
            return result

    return None if default is NO_DEFAULT else default


def dict_get(d, key_or_keys, default=None, skip_false_values=True):
    exp = (lambda x: x or None) if skip_false_values else IDENTITY
    return traverse_obj(d, *variadic(key_or_keys), expected_type=exp,
                        default=default, get_all=False)


def get_first(obj, keys, **kwargs):
    return traverse_obj(obj, (Ellipsis,) + tuple(variadic(keys)), get_all=False, **kwargs)


def T(*x):
    """ For use in yt-dl instead of {type, ...} or set((type, ...)) """
    return set(x)
