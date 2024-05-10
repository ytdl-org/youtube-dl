# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..compat import compat_kwargs
from ..utils import (
    base_url,
    determine_ext,
    ExtractorError,
    float_or_none,
    merge_dicts,
    T,
    traverse_obj,
    txt_or_none,
    url_basename,
    url_or_none,
)


class Vbox7IE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?vbox7\.com/
                        (?:
                            play:|
                            (?:
                                emb/external\.php|
                                player/ext\.swf
                            )\?.*?\bvid=
                        )
                        (?P<id>[\da-fA-F]+)
                    '''
    _EMBED_REGEX = [r'<iframe[^>]+src=(?P<q>["\'])(?P<url>(?:https?:)?//vbox7\.com/emb/external\.php.+?)(?P=q)']
    _GEO_COUNTRIES = ['BG']
    _TESTS = [{
        # the http: URL just redirects here
        'url': 'https://vbox7.com/play:0946fff23c',
        'md5': '50ca1f78345a9c15391af47d8062d074',
        'info_dict': {
            'id': '0946fff23c',
            'ext': 'mp4',
            'title': 'Борисов: Притеснен съм за бъдещето на България',
            'description': 'По думите му е опасно страната ни да бъде обявена за "сигурна"',
            'timestamp': 1470982814,
            'upload_date': '20160812',
            'uploader': 'zdraveibulgaria',
            'thumbnail': r're:^https?://.*\.jpg$',
            'view_count': int,
            'duration': 2640,
        },
        'expected_warnings': [
            'Unable to download webpage',
        ],
    }, {
        'url': 'http://vbox7.com/play:249bb972c2',
        'md5': '99f65c0c9ef9b682b97313e052734c3f',
        'info_dict': {
            'id': '249bb972c2',
            'ext': 'mp4',
            'title': 'Смях! Чудо - чист за секунди - Скрита камера',
            'description': 'Смях! Чудо - чист за секунди - Скрита камера',
            'timestamp': 1360215023,
            'upload_date': '20130207',
            'uploader': 'svideteliat_ot_varshava',
            'thumbnail': 'https://i49.vbox7.com/o/249/249bb972c20.jpg',
            'view_count': int,
            'duration': 83,
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://vbox7.com/emb/external.php?vid=a240d20f9c&autoplay=1',
        'only_matching': True,
    }, {
        'url': 'http://i49.vbox7.com/player/ext.swf?vid=0946fff23c&autoplay=1',
        'only_matching': True,
    }]

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(cls._EMBED_REGEX[0], webpage)
        if mobj:
            return mobj.group('url')

    # specialisation to transform what looks like ld+json that
    # may contain invalid character combinations

    # transform_source=None, fatal=True
    def _parse_json(self, json_string, video_id, *args, **kwargs):
        if '"@context"' in json_string[:30]:
            # this is ld+json, or that's the way to bet
            transform_source = args[0] if len(args) > 0 else kwargs.get('transform_source')
            if not transform_source:

                def fix_chars(src):
                    # fix malformed ld+json: replace raw CRLFs with escaped LFs
                    return re.sub(
                        r'"[^"]+"', lambda m: re.sub(r'\r?\n', r'\\n', m.group(0)), src)

                if len(args) > 0:
                    args = (fix_chars,) + args[1:]
                else:
                    kwargs['transform_source'] = fix_chars
                    kwargs = compat_kwargs(kwargs)

        return super(Vbox7IE, self)._parse_json(
            json_string, video_id, *args, **kwargs)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://vbox7.com/play:%s' % (video_id,)

        now = time.time()
        response = self._download_json(
            'https://www.vbox7.com/aj/player/item/options', video_id,
            query={'vid': video_id}, headers={'Referer': url})
        # estimate time to which possible `ago` member is relative
        now = now + 0.5 * (time.time() - now)

        if traverse_obj(response, 'error'):
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, response['error']), expected=True)

        src_url = traverse_obj(response, ('options', 'src', T(url_or_none))) or ''

        fmt_base = url_basename(src_url).rsplit('.', 1)[0].rsplit('_', 1)[0]
        if fmt_base in ('na', 'vn'):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        ext = determine_ext(src_url)
        if ext == 'mpd':
            # extract MPD
            try:
                formats, subtitles = self._extract_mpd_formats_and_subtitles(
                    src_url, video_id, 'dash', fatal=False)
            except KeyError:  # fatal doesn't catch this
                self.report_warning('Failed to parse MPD manifest')
                formats, subtitles = [], {}
        elif ext != 'm3u8':
            formats = [{
                'url': src_url,
            }] if src_url else []
            subtitles = {}

        if src_url:
            # possibly extract HLS, based on https://github.com/yt-dlp/yt-dlp/pull/9100
            fmt_base = base_url(src_url) + fmt_base
            # prepare for _extract_m3u8_formats_and_subtitles()
            # hls_formats, hls_subs = self._extract_m3u8_formats_and_subtitles(
            hls_formats = self._extract_m3u8_formats(
                '{0}.m3u8'.format(fmt_base), video_id, m3u8_id='hls', fatal=False)
            formats.extend(hls_formats)
            # self._merge_subtitles(hls_subs, target=subtitles)

            # In case MPD/HLS cannot be parsed, or anyway, get mp4 combined
            # formats usually provided to Safari, iOS, and old Windows
            video = response['options']
            resolutions = (1080, 720, 480, 240, 144)
            highest_res = traverse_obj(video, (
                'highestRes', T(int))) or resolutions[0]
            resolutions = traverse_obj(video, (
                'resolutions', lambda _, r: highest_res >= int(r) > 0)) or resolutions
            mp4_formats = traverse_obj(resolutions, (
                Ellipsis, T(lambda res: {
                    'url': '{0}_{1}.mp4'.format(fmt_base, res),
                    'format_id': 'http-{0}'.format(res),
                    'height': res,
                })))
            # if above formats are flaky, enable the line below
            # self._check_formats(mp4_formats, video_id)
            formats.extend(mp4_formats)

        self._sort_formats(formats)

        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        info = self._search_json_ld(
            webpage.replace('"/*@context"', '"@context"'), video_id,
            fatal=False) if webpage else {}

        if not info.get('title'):
            info['title'] = traverse_obj(response, (
                'options', 'title', T(txt_or_none))) or self._og_search_title(webpage)

        def if_missing(k):
            return lambda x: None if k in info else x

        info = merge_dicts(info, {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles or None,
        }, info, traverse_obj(response, ('options', {
            'uploader': ('uploader', T(txt_or_none)),
            'timestamp': ('ago', T(if_missing('timestamp')), T(lambda t: int(round((now - t) / 60.0)) * 60)),
            'duration': ('duration', T(if_missing('duration')), T(float_or_none)),
        })))
        if 'thumbnail' not in info:
            info['thumbnail'] = self._proto_relative_url(
                info.get('thumbnail') or self._og_search_thumbnail(webpage),
                'https:'),

        return info
