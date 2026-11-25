# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_kwargs,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    smuggle_url,
    str_or_none,
)

try:
    from ..utils import traverse_obj
except ImportError:
    from ..compat import compat_collections_abc

    def traverse_obj(obj, *path_list, **kw):
        ''' Traverse nested list/dict/tuple'''

        # parameter defaults
        default = kw.get('default')
        expected_type = kw.get('expected_type')
        get_all = kw.get('get_all', True)
        casesense = kw.get('casesense', True)
        is_user_input = kw.get('is_user_input', False)
        traverse_string = kw.get('traverse_string', False)

        def variadic(x, allowed_types=(compat_str, bytes)):
            return x if isinstance(x, compat_collections_abc.Iterable) and not isinstance(x, allowed_types) else (x,)

        def listish(l):
            return isinstance(l, (list, tuple))

        def from_iterable(iterables):
            # chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
            for it in iterables:
                for element in it:
                    yield element

        class Nonlocal:
            pass
        nl = Nonlocal()

        if not casesense:
            _lower = lambda k: (k.lower() if isinstance(k, compat_str) else k)
            path_list = (map(_lower, variadic(path)) for path in path_list)

        def _traverse_obj(obj, path, _current_depth=0):
            path = tuple(variadic(path))
            for i, key in enumerate(path):
                if obj is None:
                    return None
                if listish(key):
                    obj = [_traverse_obj(obj, sub_key, _current_depth) for sub_key in key]
                    key = Ellipsis
                if key is Ellipsis:
                    obj = (obj.values() if isinstance(obj, dict)
                           else obj if listish(obj)
                           else compat_str(obj) if traverse_string else [])
                    _current_depth += 1
                    nl.depth = max(nl.depth, _current_depth)
                    return [_traverse_obj(inner_obj, path[i + 1:], _current_depth) for inner_obj in obj]
                elif callable(key):
                    if listish(obj):
                        obj = enumerate(obj)
                    elif isinstance(obj, dict):
                        obj = obj.items()
                    else:
                        if not traverse_string:
                            return None
                        obj = str(obj)
                    _current_depth += 1
                    nl.depth = max(nl.depth, _current_depth)
                    return [_traverse_obj(v, path[i + 1:], _current_depth) for k, v in obj if key(k)]
                elif isinstance(obj, dict) and not (is_user_input and key == ':'):
                    obj = (obj.get(key) if casesense or (key in obj)
                           else next((v for k, v in obj.items() if _lower(k) == key), None))
                else:
                    if is_user_input:
                        key = (int_or_none(key) if ':' not in key
                               else slice(*map(int_or_none, key.split(':'))))
                        if key == slice(None):
                            return _traverse_obj(obj, tuple([Ellipsis] + list(path[i + 1:])), _current_depth)
                    if not isinstance(key, (int, slice)):
                        return None
                    if not listish(obj):
                        if not traverse_string:
                            return None
                        obj = compat_str(obj)
                    try:
                        obj = obj[key]
                    except IndexError:
                        return None
            return obj

        if isinstance(expected_type, type):
            type_test = lambda val: val if isinstance(val, expected_type) else None
        elif expected_type is not None:
            type_test = expected_type
        else:
            type_test = lambda val: val

        for path in path_list:
            nl.depth = 0
            val = _traverse_obj(obj, path)
            if val is not None:
                if nl.depth:
                    for _ in range(nl.depth - 1):
                        val = from_iterable(v for v in val if v is not None)
                    val = [v for v in map(type_test, val) if v is not None]
                    if val:
                        return val if get_all else val[0]
                else:
                    val = type_test(val)
                    if val is not None:
                        return val
        return default


class TVerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tver\.jp/(?:(?P<type>lp|corner|series|episodes?|feature|tokyo2020/video)/)+(?P<id>[a-zA-Z0-9]+)'
    # videos are only available for 7 days
    _TESTS = [{
        'skip': 'videos are only available for 7 days',
        'url': 'https://tver.jp/episodes/ephss8yveb',
        'info_dict': {
            'id': 'ref:af03de03-21ac-4b98-a53b-9ffd9b102e92',
            'ext': 'mp4',
            'title': '#44　料理と値段と店主にびっくり　オモてなしすぎウマい店　2時間SP',
            'description': 'md5:66985373a66fed8ad3cd595a3cfebb13',
            'upload_date': '20220329',
            'uploader_id': '4394098882001',
            'timestamp': 1648527032,
        },
        'add_ie': ['BrightcoveNew'],
    }, {
        'skip': 'videos are only available for 7 days',
        'url': 'https://tver.jp/lp/episodes/ep6f16g26p',
        'info_dict': {
            'id': '6302378806001',
            'ext': 'mp4',
            # "April 11 (Mon) 23:06-Broadcast scheduled": sorry but this is "correct"
            'title': '4月11日(月)23時06分 ~ 放送予定',
            'description': 'md5:4029cc5f4b1e8090dfc5b7bd2bc5cd0b',
            'upload_date': '20220331',
            'uploader_id': '3971130137001',
            'timestamp': 1648696456,
        },
        'add_ie': ['BrightcoveNew'],
    }, {
        'url': 'https://tver.jp/corner/f0103888',
        'only_matching': True,
    }, {
        'url': 'https://tver.jp/lp/f0033031',
        'only_matching': True,
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s'
    _PLATFORM_UID = None
    _PLATFORM_TOKEN = None

    def _download_json(self, url_or_request, video_id, **kwargs):

        headers = {
            'Origin': 'https://s.tver.jp',
            'Referer': 'https://s.tver.jp/',
        }
        headers.update(kwargs.get('headers', {}))
        kwargs.update(compat_kwargs({'headers': headers, }))

        return super(TVerIE, self)._download_json(url_or_request, video_id, **kwargs)

    def _real_initialize(self):
        create_response = self._download_json(
            'https://platform-api.tver.jp/v2/api/platform_users/browser/create', None,
            note='Creating session', data=b'device_type=pc', headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            })
        self._PLATFORM_UID = traverse_obj(create_response, ('result', 'platform_uid'), expected_type=compat_str)
        self._PLATFORM_TOKEN = traverse_obj(create_response, ('result', 'platform_token'), expected_type=compat_str)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_id, video_type = re.match(self._VALID_URL, url).group('id', 'type')
        if video_type not in ('episode', 'episodes', 'series'):
            webpage = self._download_webpage(url, video_id, note='Resolving to new URL')
            video_id = self._match_id(self._search_regex(
                (r'''canonical['"]\s+href\s*=\s*(?P<q>'|")(?P<url>https?://tver\.jp/(?!(?P=q)).+?)(?P=q)''',
                 r'&link=(?P<url>https?://tver\.jp/(?!(?P=q)).+?)[?&]'),
                webpage, 'url regex', group='url'))
        video_info = self._download_json(
            'https://statics.tver.jp/content/episode/{0}.json'.format(video_id), video_id,
            query={'v': '5'})
        p_id = traverse_obj(video_info, ('video', 'accountID'), expected_type=compat_str)
        r_id = traverse_obj(video_info, ('video', ('videoRefID', 'videoID')), get_all=False, expected_type=compat_str)
        if None in (p_id, r_id):
            raise ExtractorError(
                'Failed to extract '
                + ', '.join(
                    (x[0] for x in (('accountID', p_id), ('videoRefID', r_id), )
                     if x[1] is None)),
                expected=False)
        if not r_id.isdigit():
            r_id = 'ref:' + r_id

        additional_info = self._download_json(
            'https://platform-api.tver.jp/service/api/v1/callEpisode/{0}?require_data=mylist,later[epefy106ur],good[epefy106ur],resume[epefy106ur]'.format(video_id),
            video_id, fatal=False,
            query={
                'platform_uid': self._PLATFORM_UID,
                'platform_token': self._PLATFORM_TOKEN,
            }, headers={
                'x-tver-platform-type': 'web'
            })

        return {
            '_type': 'url_transparent',
            'title': str_or_none(video_info.get('title')),
            'description': str_or_none(video_info.get('description')),
            'url': smuggle_url(
                self.BRIGHTCOVE_URL_TEMPLATE % (p_id, r_id), {'geo_countries': ['JP']}),
            'series': traverse_obj(
                additional_info, ('result', ('episode', 'series'), 'content', ('seriesTitle', 'title')),
                get_all=False, expected_type=compat_str),
            'ie_key': 'BrightcoveNew',
        }
