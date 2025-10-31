#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import itertools
import re

from youtube_dl.traversal import (
    dict_get,
    get_first,
    require,
    T,
    traverse_obj,
    unpack,
    value,
)
from youtube_dl.compat import (
    compat_chr as chr,
    compat_etree_fromstring,
    compat_http_cookies,
    compat_map as map,
    compat_str,
    compat_zip as zip,
)
from youtube_dl.utils import (
    ExtractorError,
    int_or_none,
    join_nonempty,
    str_or_none,
)

_TEST_DATA = {
    100: 100,
    1.2: 1.2,
    'str': 'str',
    'None': None,
    '...': Ellipsis,
    'urls': [
        {'index': 0, 'url': 'https://www.example.com/0'},
        {'index': 1, 'url': 'https://www.example.com/1'},
    ],
    'data': (
        {'index': 2},
        {'index': 3},
    ),
    'dict': {},
}


if sys.version_info < (3, 0):
    class _TestCase(unittest.TestCase):

        def assertCountEqual(self, *args, **kwargs):
            return self.assertItemsEqual(*args, **kwargs)
else:
    _TestCase = unittest.TestCase


class TestTraversal(_TestCase):
    def assertMaybeCountEqual(self, *args, **kwargs):
        if sys.version_info < (3, 7):
            # random dict order
            return self.assertCountEqual(*args, **kwargs)
        else:
            return self.assertEqual(*args, **kwargs)

    def test_traverse_obj(self):
        # instant compat
        str = compat_str

        # define a pukka Iterable
        def iter_range(stop):
            for from_ in range(stop):
                yield from_

        # Test base functionality
        self.assertEqual(traverse_obj(_TEST_DATA, ('str',)), 'str',
                         msg='allow tuple path')
        self.assertEqual(traverse_obj(_TEST_DATA, ['str']), 'str',
                         msg='allow list path')
        self.assertEqual(traverse_obj(_TEST_DATA, (value for value in ("str",))), 'str',
                         msg='allow iterable path')
        self.assertEqual(traverse_obj(_TEST_DATA, 'str'), 'str',
                         msg='single items should be treated as a path')
        self.assertEqual(traverse_obj(_TEST_DATA, None), _TEST_DATA)
        self.assertEqual(traverse_obj(_TEST_DATA, 100), 100)
        self.assertEqual(traverse_obj(_TEST_DATA, 1.2), 1.2)

        # Test Ellipsis behavior
        self.assertCountEqual(traverse_obj(_TEST_DATA, Ellipsis),
                              (item for item in _TEST_DATA.values() if item not in (None, {})),
                              msg='`...` should give all non-discarded values')
        self.assertCountEqual(traverse_obj(_TEST_DATA, ('urls', 0, Ellipsis)), _TEST_DATA['urls'][0].values(),
                              msg='`...` selection for dicts should select all values')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, Ellipsis, 'url')),
                         ['https://www.example.com/0', 'https://www.example.com/1'],
                         msg='nested `...` queries should work')
        self.assertCountEqual(traverse_obj(_TEST_DATA, (Ellipsis, Ellipsis, 'index')), iter_range(4),
                              msg='`...` query result should be flattened')
        self.assertEqual(traverse_obj(iter(range(4)), Ellipsis), list(range(4)),
                         msg='`...` should accept iterables')

        # Test function as key
        self.assertEqual(traverse_obj(_TEST_DATA, lambda x, y: x == 'urls' and isinstance(y, list)),
                         [_TEST_DATA['urls']],
                         msg='function as query key should perform a filter based on (key, value)')
        self.assertCountEqual(traverse_obj(_TEST_DATA, lambda _, x: isinstance(x[0], str)), set(('str',)),
                              msg='exceptions in the query function should be caught')
        self.assertEqual(traverse_obj(iter(range(4)), lambda _, x: x % 2 == 0), [0, 2],
                         msg='function key should accept iterables')
        if __debug__:
            with self.assertRaises(Exception, msg='Wrong function signature should raise in debug'):
                traverse_obj(_TEST_DATA, lambda a: Ellipsis)
            with self.assertRaises(Exception, msg='Wrong function signature should raise in debug'):
                traverse_obj(_TEST_DATA, lambda a, b, c: Ellipsis)

        # Test set as key (transformation/type, like `expected_type`)
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, T(str.upper), )), ['STR'],
                         msg='Function in set should be a transformation')
        self.assertEqual(traverse_obj(_TEST_DATA, ('fail', T(lambda _: 'const'))), 'const',
                         msg='Function in set should always be called')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, T(str))), ['str'],
                         msg='Type in set should be a type filter')
        self.assertMaybeCountEqual(traverse_obj(_TEST_DATA, (Ellipsis, T(str, int))), [100, 'str'],
                                   msg='Multiple types in set should be a type filter')
        self.assertEqual(traverse_obj(_TEST_DATA, T(dict)), _TEST_DATA,
                         msg='A single set should be wrapped into a path')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, T(str.upper))), ['STR'],
                         msg='Transformation function should not raise')
        self.assertMaybeCountEqual(traverse_obj(_TEST_DATA, (Ellipsis, T(str_or_none))),
                                   [item for item in map(str_or_none, _TEST_DATA.values()) if item is not None],
                                   msg='Function in set should be a transformation')
        if __debug__:
            with self.assertRaises(Exception, msg='Sets with length != 1 should raise in debug'):
                traverse_obj(_TEST_DATA, set())
            with self.assertRaises(Exception, msg='Sets with length != 1 should raise in debug'):
                traverse_obj(_TEST_DATA, set((str.upper, str)))

        # Test `slice` as a key
        _SLICE_DATA = [0, 1, 2, 3, 4]
        self.assertEqual(traverse_obj(_TEST_DATA, ('dict', slice(1))), None,
                         msg='slice on a dictionary should not throw')
        self.assertEqual(traverse_obj(_SLICE_DATA, slice(1)), _SLICE_DATA[:1],
                         msg='slice key should apply slice to sequence')
        self.assertEqual(traverse_obj(_SLICE_DATA, slice(1, 2)), _SLICE_DATA[1:2],
                         msg='slice key should apply slice to sequence')
        self.assertEqual(traverse_obj(_SLICE_DATA, slice(1, 4, 2)), _SLICE_DATA[1:4:2],
                         msg='slice key should apply slice to sequence')

        # Test alternative paths
        self.assertEqual(traverse_obj(_TEST_DATA, 'fail', 'str'), 'str',
                         msg='multiple `paths` should be treated as alternative paths')
        self.assertEqual(traverse_obj(_TEST_DATA, 'str', 100), 'str',
                         msg='alternatives should exit early')
        self.assertEqual(traverse_obj(_TEST_DATA, 'fail', 'fail'), None,
                         msg='alternatives should return `default` if exhausted')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, 'fail'), 100), 100,
                         msg='alternatives should track their own branching return')
        self.assertEqual(traverse_obj(_TEST_DATA, ('dict', Ellipsis), ('data', Ellipsis)), list(_TEST_DATA['data']),
                         msg='alternatives on empty objects should search further')

        # Test branch and path nesting
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', (3, 0), 'url')), ['https://www.example.com/0'],
                         msg='tuple as key should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', [3, 0], 'url')), ['https://www.example.com/0'],
                         msg='list as key should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', ((1, 'fail'), (0, 'url')))), ['https://www.example.com/0'],
                         msg='double nesting in path should be treated as paths')
        self.assertEqual(traverse_obj(['0', [1, 2]], [(0, 1), 0]), [1],
                         msg='do not fail early on branching')
        self.assertCountEqual(traverse_obj(_TEST_DATA, ('urls', ((1, ('fail', 'url')), (0, 'url')))),
                              ['https://www.example.com/0', 'https://www.example.com/1'],
                              msg='triple nesting in path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', ('fail', (Ellipsis, 'url')))),
                         ['https://www.example.com/0', 'https://www.example.com/1'],
                         msg='ellipsis as branch path start gets flattened')

        # Test dictionary as key
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 100, 1: 1.2}), {0: 100, 1: 1.2},
                         msg='dict key should result in a dict with the same keys')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', 0, 'url')}),
                         {0: 'https://www.example.com/0'},
                         msg='dict key should allow paths')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', (3, 0), 'url')}),
                         {0: ['https://www.example.com/0']},
                         msg='tuple in dict path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', ((1, 'fail'), (0, 'url')))}),
                         {0: ['https://www.example.com/0']},
                         msg='double nesting in dict path should be treated as paths')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', ((1, ('fail', 'url')), (0, 'url')))}),
                         {0: ['https://www.example.com/1', 'https://www.example.com/0']},
                         msg='triple nesting in dict path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'fail'}), {},
                         msg='remove `None` values when top level dict key fails')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'fail'}, default=Ellipsis), {0: Ellipsis},
                         msg='use `default` if key fails and `default`')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'dict'}), {},
                         msg='remove empty values when dict key')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'dict'}, default=Ellipsis), {0: Ellipsis},
                         msg='use `default` when dict key and a default')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: {0: 'fail'}}), {},
                         msg='remove empty values when nested dict key fails')
        self.assertEqual(traverse_obj(None, {0: 'fail'}), {},
                         msg='default to dict if pruned')
        self.assertEqual(traverse_obj(None, {0: 'fail'}, default=Ellipsis), {0: Ellipsis},
                         msg='default to dict if pruned and default is given')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: {0: 'fail'}}, default=Ellipsis), {0: {0: Ellipsis}},
                         msg='use nested `default` when nested dict key fails and `default`')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('dict', Ellipsis)}), {},
                         msg='remove key if branch in dict key not successful')

        # Testing default parameter behavior
        _DEFAULT_DATA = {'None': None, 'int': 0, 'list': []}
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail'), None,
                         msg='default value should be `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail', 'fail', default=Ellipsis), Ellipsis,
                         msg='chained fails should result in default')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'None', 'int'), 0,
                         msg='should not short cirquit on `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail', default=1), 1,
                         msg='invalid dict key should result in `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'None', default=1), 1,
                         msg='`None` is a deliberate sentinel and should become `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, ('list', 10)), None,
                         msg='`IndexError` should result in `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail'), default=1), 1,
                         msg='if branched but not successful return `default` if defined, not `[]`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail'), default=None), None,
                         msg='if branched but not successful return `default` even if `default` is `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail')), [],
                         msg='if branched but not successful return `[]`, not `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, ('list', Ellipsis)), [],
                         msg='if branched but object is empty return `[]`, not `default`')
        self.assertEqual(traverse_obj(None, Ellipsis), [],
                         msg='if branched but object is `None` return `[]`, not `default`')
        self.assertEqual(traverse_obj({0: None}, (0, Ellipsis)), [],
                         msg='if branched but state is `None` return `[]`, not `default`')

        branching_paths = [
            ('fail', Ellipsis),
            (Ellipsis, 'fail'),
            100 * ('fail',) + (Ellipsis,),
            (Ellipsis,) + 100 * ('fail',),
        ]
        for branching_path in branching_paths:
            self.assertEqual(traverse_obj({}, branching_path), [],
                             msg='if branched but state is `None`, return `[]` (not `default`)')
            self.assertEqual(traverse_obj({}, 'fail', branching_path), [],
                             msg='if branching in last alternative and previous did not match, return `[]` (not `default`)')
            self.assertEqual(traverse_obj({0: 'x'}, 0, branching_path), 'x',
                             msg='if branching in last alternative and previous did match, return single value')
            self.assertEqual(traverse_obj({0: 'x'}, branching_path, 0), 'x',
                             msg='if branching in first alternative and non-branching path does match, return single value')
            self.assertEqual(traverse_obj({}, branching_path, 'fail'), None,
                             msg='if branching in first alternative and non-branching path does not match, return `default`')

        # Testing expected_type behavior
        _EXPECTED_TYPE_DATA = {'str': 'str', 'int': 0}
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=str),
                         'str', msg='accept matching `expected_type` type')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=int),
                         None, msg='reject non-matching `expected_type` type')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'int', expected_type=lambda x: str(x)),
                         '0', msg='transform type using type function')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=lambda _: 1 / 0),
                         None, msg='wrap expected_type function in try_call')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, Ellipsis, expected_type=str),
                         ['str'], msg='eliminate items that expected_type fails on')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 100, 1: 1.2}, expected_type=int),
                         {0: 100}, msg='type as expected_type should filter dict values')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 100, 1: 1.2, 2: 'None'}, expected_type=str_or_none),
                         {0: '100', 1: '1.2'}, msg='function as expected_type should transform dict values')
        self.assertEqual(traverse_obj(_TEST_DATA, ({0: 1.2}, 0, set((int_or_none,))), expected_type=int),
                         1, msg='expected_type should not filter non-final dict values')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: {0: 100, 1: 'str'}}, expected_type=int),
                         {0: {0: 100}}, msg='expected_type should transform deep dict values')
        self.assertEqual(traverse_obj(_TEST_DATA, [({0: '...'}, {0: '...'})], expected_type=type(Ellipsis)),
                         [{0: Ellipsis}, {0: Ellipsis}], msg='expected_type should transform branched dict values')
        self.assertEqual(traverse_obj({1: {3: 4}}, [(1, 2), 3], expected_type=int),
                         [4], msg='expected_type regression for type matching in tuple branching')
        self.assertEqual(traverse_obj(_TEST_DATA, ['data', Ellipsis], expected_type=int),
                         [], msg='expected_type regression for type matching in dict result')

        # Test get_all behavior
        _GET_ALL_DATA = {'key': [0, 1, 2]}
        self.assertEqual(traverse_obj(_GET_ALL_DATA, ('key', Ellipsis), get_all=False), 0,
                         msg='if not `get_all`, return only first matching value')
        self.assertEqual(traverse_obj(_GET_ALL_DATA, Ellipsis, get_all=False), [0, 1, 2],
                         msg='do not overflatten if not `get_all`')

        # Test casesense behavior
        _CASESENSE_DATA = {
            'KeY': 'value0',
            0: {
                'KeY': 'value1',
                0: {'KeY': 'value2'},
            },
            # FULLWIDTH LATIN CAPITAL LETTER K
            '\uff2bey': 'value3',
        }
        self.assertEqual(traverse_obj(_CASESENSE_DATA, 'key'), None,
                         msg='dict keys should be case sensitive unless `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, 'keY',
                                      casesense=False), 'value0',
                         msg='allow non matching key case if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, '\uff4bey',  # FULLWIDTH LATIN SMALL LETTER K
                                      casesense=False), 'value3',
                         msg='allow non matching Unicode key case if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, (0, ('keY',)),
                                      casesense=False), ['value1'],
                         msg='allow non matching key case in branch if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, (0, ((0, 'keY'),)),
                                      casesense=False), ['value2'],
                         msg='allow non matching key case in branch path if `casesense`')

        # Test traverse_string behavior
        _TRAVERSE_STRING_DATA = {'str': 'str', 1.2: 1.2}
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0)), None,
                         msg='do not traverse into string if not `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0),
                                      _traverse_string=True), 's',
                         msg='traverse into string if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, (1.2, 1),
                                      _traverse_string=True), '.',
                         msg='traverse into converted data if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', Ellipsis),
                                      _traverse_string=True), 'str',
                         msg='`...` should result in string (same value) if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', slice(0, None, 2)),
                                      _traverse_string=True), 'sr',
                         msg='`slice` should result in string if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', lambda i, v: i or v == 's'),
                                      _traverse_string=True), 'str',
                         msg='function should result in string if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', (0, 2)),
                                      _traverse_string=True), ['s', 'r'],
                         msg='branching should result in list if `traverse_string`')
        self.assertEqual(traverse_obj({}, (0, Ellipsis), _traverse_string=True), [],
                         msg='branching should result in list if `traverse_string`')
        self.assertEqual(traverse_obj({}, (0, lambda x, y: True), _traverse_string=True), [],
                         msg='branching should result in list if `traverse_string`')
        self.assertEqual(traverse_obj({}, (0, slice(1)), _traverse_string=True), [],
                         msg='branching should result in list if `traverse_string`')

        # Test re.Match as input obj
        mobj = re.match(r'^0(12)(?P<group>3)(4)?$', '0123')
        self.assertEqual(traverse_obj(mobj, Ellipsis), [x for x in mobj.groups() if x is not None],
                         msg='`...` on a `re.Match` should give its `groups()`')
        self.assertEqual(traverse_obj(mobj, lambda k, _: k in (0, 2)), ['0123', '3'],
                         msg='function on a `re.Match` should give groupno, value starting at 0')
        self.assertEqual(traverse_obj(mobj, 'group'), '3',
                         msg='str key on a `re.Match` should give group with that name')
        self.assertEqual(traverse_obj(mobj, 2), '3',
                         msg='int key on a `re.Match` should give group with that name')
        self.assertEqual(traverse_obj(mobj, 'gRoUp', casesense=False), '3',
                         msg='str key on a `re.Match` should respect casesense')
        self.assertEqual(traverse_obj(mobj, 'fail'), None,
                         msg='failing str key on a `re.Match` should return `default`')
        self.assertEqual(traverse_obj(mobj, 'gRoUpS', casesense=False), None,
                         msg='failing str key on a `re.Match` should return `default`')
        self.assertEqual(traverse_obj(mobj, 8), None,
                         msg='failing int key on a `re.Match` should return `default`')
        self.assertEqual(traverse_obj(mobj, lambda k, _: k in (0, 'group')), ['0123', '3'],
                         msg='function on a `re.Match` should give group name as well')

        # Test xml.etree.ElementTree.Element as input obj
        etree = compat_etree_fromstring('''<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
                <year>2008</year>
                <gdppc>141100</gdppc>
                <neighbor name="Austria" direction="E"/>
                <neighbor name="Switzerland" direction="W"/>
            </country>
            <country name="Singapore">
                <rank>4</rank>
                <year>2011</year>
                <gdppc>59900</gdppc>
                <neighbor name="Malaysia" direction="N"/>
            </country>
            <country name="Panama">
                <rank>68</rank>
                <year>2011</year>
                <gdppc>13600</gdppc>
                <neighbor name="Costa Rica" direction="W"/>
                <neighbor name="Colombia" direction="E"/>
            </country>
        </data>''')
        self.assertEqual(traverse_obj(etree, ''), etree,
                         msg='empty str key should return the element itself')
        self.assertEqual(traverse_obj(etree, 'country'), list(etree),
                         msg='str key should return all children with that tag name')
        self.assertEqual(traverse_obj(etree, Ellipsis), list(etree),
                         msg='`...` as key should return all children')
        self.assertEqual(traverse_obj(etree, lambda _, x: x[0].text == '4'), [etree[1]],
                         msg='function as key should get element as value')
        self.assertEqual(traverse_obj(etree, lambda i, _: i == 1), [etree[1]],
                         msg='function as key should get index as key')
        self.assertEqual(traverse_obj(etree, 0), etree[0],
                         msg='int key should return the nth child')
        self.assertEqual(traverse_obj(etree, './/neighbor/@name'),
                         ['Austria', 'Switzerland', 'Malaysia', 'Costa Rica', 'Colombia'],
                         msg='`@<attribute>` at end of path should give that attribute')
        self.assertEqual(traverse_obj(etree, '//neighbor/@fail'), [None, None, None, None, None],
                         msg='`@<nonexistent>` at end of path should give `None`')
        self.assertEqual(traverse_obj(etree, ('//neighbor/@', 2)), {'name': 'Malaysia', 'direction': 'N'},
                         msg='`@` should give the full attribute dict')
        self.assertEqual(traverse_obj(etree, '//year/text()'), ['2008', '2011', '2011'],
                         msg='`text()` at end of path should give the inner text')
        self.assertEqual(traverse_obj(etree, '//*[@direction]/@direction'), ['E', 'W', 'N', 'W', 'E'],
                         msg='full python xpath features should be supported')
        self.assertEqual(traverse_obj(etree, (0, '@name')), 'Liechtenstein',
                         msg='special transformations should act on current element')
        self.assertEqual(traverse_obj(etree, ('country', 0, Ellipsis, 'text()', T(int_or_none))), [1, 2008, 141100],
                         msg='special transformations should act on current element')

    def test_traversal_unbranching(self):
        self.assertEqual(traverse_obj(_TEST_DATA, [(100, 1.2), all]), [100, 1.2],
                         msg='`all` should give all results as list')
        self.assertEqual(traverse_obj(_TEST_DATA, [(100, 1.2), any]), 100,
                         msg='`any` should give the first result')
        self.assertEqual(traverse_obj(_TEST_DATA, [100, all]), [100],
                         msg='`all` should give list if non branching')
        self.assertEqual(traverse_obj(_TEST_DATA, [100, any]), 100,
                         msg='`any` should give single item if non branching')
        self.assertEqual(traverse_obj(_TEST_DATA, [('dict', 'None', 100), all]), [100],
                         msg='`all` should filter `None` and empty dict')
        self.assertEqual(traverse_obj(_TEST_DATA, [('dict', 'None', 100), any]), 100,
                         msg='`any` should filter `None` and empty dict')
        self.assertEqual(traverse_obj(_TEST_DATA, [{
            'all': [('dict', 'None', 100, 1.2), all],
            'any': [('dict', 'None', 100, 1.2), any],
        }]), {'all': [100, 1.2], 'any': 100},
            msg='`all`/`any` should apply to each dict path separately')
        self.assertEqual(traverse_obj(_TEST_DATA, [{
            'all': [('dict', 'None', 100, 1.2), all],
            'any': [('dict', 'None', 100, 1.2), any],
        }], get_all=False), {'all': [100, 1.2], 'any': 100},
            msg='`all`/`any` should apply to dict regardless of `get_all`')
        self.assertIs(traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), all, T(float)]), None,
                      msg='`all` should reset branching status')
        self.assertIs(traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), any, T(float)]), None,
                      msg='`any` should reset branching status')
        self.assertEqual(traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), all, Ellipsis, T(float)]), [1.2],
                         msg='`all` should allow further branching')
        self.assertEqual(traverse_obj(_TEST_DATA, [('dict', 'None', 'urls', 'data'), any, Ellipsis, 'index']), [0, 1],
                         msg='`any` should allow further branching')

    def test_traversal_morsel(self):
        morsel = compat_http_cookies.Morsel()
        # SameSite added in Py3.8, breaks .update for 3.5-3.7
        # Similarly Partitioned, Py3.14, thx Grub4k
        values = dict(zip(morsel, map(chr, itertools.count(ord('a')))))
        morsel.set(str('item_key'), 'item_value', 'coded_value')
        morsel.update(values)
        values.update({
            'key': str('item_key'),
            'value': 'item_value',
        }),
        values = dict((str(k), v) for k, v in values.items())

        for key, val in values.items():
            self.assertEqual(traverse_obj(morsel, key), val,
                             msg='Morsel should provide access to all values')
        values = list(values.values())
        self.assertMaybeCountEqual(traverse_obj(morsel, Ellipsis), values,
                                   msg='`...` should yield all values')
        self.assertMaybeCountEqual(traverse_obj(morsel, lambda k, v: True), values,
                                   msg='function key should yield all values')
        self.assertIs(traverse_obj(morsel, [(None,), any]), morsel,
                      msg='Morsel should not be implicitly changed to dict on usage')

    def test_traversal_filter(self):
        data = [None, False, True, 0, 1, 0.0, 1.1, '', 'str', {}, {0: 0}, [], [1]]

        self.assertEqual(
            traverse_obj(data, (Ellipsis, filter)),
            [True, 1, 1.1, 'str', {0: 0}, [1]],
            '`filter` should filter falsy values')


class TestTraversalHelpers(_TestCase):
    def test_traversal_require(self):
        with self.assertRaises(ExtractorError, msg='Missing `value` should raise'):
            traverse_obj(_TEST_DATA, ('None', T(require('value'))))
        self.assertEqual(
            traverse_obj(_TEST_DATA, ('str', T(require('value')))), 'str',
            '`require` should pass through non-`None` values')

    def test_unpack(self):
        self.assertEqual(
            unpack(lambda *x: ''.join(map(compat_str, x)))([1, 2, 3]), '123')
        self.assertEqual(
            unpack(join_nonempty)([1, 2, 3]), '1-2-3')
        self.assertEqual(
            unpack(join_nonempty, delim=' ')([1, 2, 3]), '1 2 3')
        with self.assertRaises(TypeError):
            unpack(join_nonempty)()
        with self.assertRaises(TypeError):
            unpack()

    def test_value(self):
        self.assertEqual(
            traverse_obj(_TEST_DATA, ('str', T(value('other')))), 'other',
            '`value` should substitute specified value')


class TestDictGet(_TestCase):
    def test_dict_get(self):
        FALSE_VALUES = {
            'none': None,
            'false': False,
            'zero': 0,
            'empty_string': '',
            'empty_list': [],
        }
        d = FALSE_VALUES.copy()
        d['a'] = 42
        self.assertEqual(dict_get(d, 'a'), 42)
        self.assertEqual(dict_get(d, 'b'), None)
        self.assertEqual(dict_get(d, 'b', 42), 42)
        self.assertEqual(dict_get(d, ('a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', 'a', 'd', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', )), None)
        self.assertEqual(dict_get(d, ('b', 'c', ), 42), 42)
        for key, false_value in FALSE_VALUES.items():
            self.assertEqual(dict_get(d, ('b', 'c', key, )), None)
            self.assertEqual(dict_get(d, ('b', 'c', key, ), skip_false_values=False), false_value)

    def test_get_first(self):
        self.assertEqual(get_first([{'a': None}, {'a': 'spam'}], 'a'), 'spam')


if __name__ == '__main__':
    unittest.main()
