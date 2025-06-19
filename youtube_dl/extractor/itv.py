# coding: utf-8
from __future__ import unicode_literals

import json
import re
import sys

from .common import InfoExtractor
from .brightcove import BrightcoveNewIE
from ..compat import (
    compat_HTTPError,
    compat_integer_types,
    compat_kwargs,
    compat_urlparse,
)
from ..utils import (
    clean_html,
    determine_ext,
    error_to_compat_str,
    extract_attributes,
    ExtractorError,
    get_element_by_attribute,
    int_or_none,
    merge_dicts,
    parse_duration,
    parse_iso8601,
    remove_start,
    smuggle_url,
    strip_or_none,
    traverse_obj,
    url_or_none,
    urljoin,
)


class ITVBaseIE(InfoExtractor):

    def __handle_request_webpage_error(self, err, video_id=None, errnote=None, fatal=True):
        if errnote is False:
            return False
        if errnote is None:
            errnote = 'Unable to download webpage'

        errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
        if fatal:
            raise ExtractorError(errmsg, sys.exc_info()[2], cause=err, video_id=video_id)
        else:
            self._downloader.report_warning(errmsg)
            return False

    @staticmethod
    def _vanilla_ua_header():
        return {'User-Agent': 'Mozilla/5.0'}

    def _download_webpage_handle(self, url, video_id, *args, **kwargs):
        # specialised to (a) use vanilla UA (b) detect geo-block
        params = self._downloader.params
        nkwargs = {}
        if (
                'user_agent' not in params
                and not any(re.match(r'(?i)user-agent\s*:', h)
                            for h in (params.get('headers') or []))
                and 'User-Agent' not in (kwargs.get('headers') or {})):

            kwargs.setdefault('headers', {})
            kwargs['headers'] = self._vanilla_ua_header()
            nkwargs = kwargs
        if kwargs.get('expected_status') is not None:
            exp = kwargs['expected_status']
            if isinstance(exp, compat_integer_types):
                exp = [exp]
            if isinstance(exp, (list, tuple)) and 403 not in exp:
                kwargs['expected_status'] = [403]
                kwargs['expected_status'].extend(exp)
                nkwargs = kwargs
        else:
            kwargs['expected_status'] = 403
            nkwargs = kwargs

        if nkwargs:
            kwargs = compat_kwargs(kwargs)

        ret = super(ITVBaseIE, self)._download_webpage_handle(url, video_id, *args, **kwargs)
        if ret is False:
            return ret
        webpage, urlh = ret

        if urlh.getcode() == 403:
            # geo-block error is like this, with an unnecessary 'Of':
            # '{\n  "Message" : "Request Originated Outside Of Allowed Geographic Region",\
            # \n  "TransactionId" : "oas-magni-475082-xbYF0W"\n}'
            if '"Request Originated Outside Of Allowed Geographic Region"' in webpage:
                self.raise_geo_restricted(countries=['GB'])
            ret = self.__handle_request_webpage_error(
                compat_HTTPError(urlh.geturl(), 403, 'HTTP Error 403: Forbidden', urlh.headers, urlh),
                fatal=kwargs.get('fatal'))

        return ret


class ITVIE(ITVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?itv\.com/(?:(?P<w>watch)|hub)/[^/]+/(?(w)[\w-]+/)(?P<id>\w+)'
    IE_DESC = 'ITVX'
    _WORKING = False

    _TESTS = [{
        'note': 'Hub URLs redirect to ITVX',
        'url': 'https://www.itv.com/hub/liar/2a4547a0012',
        'only_matching': True,
    }, {
        'note': 'Hub page unavailable via data-playlist-url (404 now)',
        'url': 'https://www.itv.com/hub/through-the-keyhole/2a2271a0033',
        'only_matching': True,
    }, {
        'note': 'Hub page with InvalidVodcrid (404 now)',
        'url': 'https://www.itv.com/hub/james-martins-saturday-morning/2a5159a0034',
        'only_matching': True,
    }, {
        'note': 'Hub page with ContentUnavailable (404 now)',
        'url': 'https://www.itv.com/hub/whos-doing-the-dishes/2a2898a0024',
        'only_matching': True,
    }, {
        'note': 'ITVX, or itvX, show',
        'url': 'https://www.itv.com/watch/vera/1a7314/1a7314a0014',
        'md5': 'bd0ad666b2c058fffe7d036785880064',
        'info_dict': {
            'id': '1a7314a0014',
            'ext': 'mp4',
            'title': 'Vera - Series 3 - Episode 4 - Prodigal Son',
            'description': 'Vera and her team investigate the fatal stabbing of an ex-Met police officer outside a busy Newcastle nightclub - but there aren\'t many clues.',
            'timestamp': 1653591600,
            'upload_date': '20220526',
            'uploader': 'ITVX',
            'thumbnail': r're:https://\w+\.itv\.com/images/(?:\w+/)+\d+x\d+\?',
            'duration': 5340.8,
            'age_limit': 16,
            'series': 'Vera',
            'series_number': 3,
            'episode': 'Prodigal Son',
            'episode_number': 4,
            'channel': 'ITV3',
            'categories': list,
        },
        'params': {
            # m3u8 download
            # 'skip_download': True,
        },
        'skip': 'only available in UK',
    }, {
        'note': 'Latest ITV news bulletin: details change daily',
        'url': 'https://www.itv.com/watch/news/varies-but-is-not-checked/6js5d0f',
        'info_dict': {
            'id': '6js5d0f',
            'ext': 'mp4',
            'title': r're:The latest ITV News headlines - \S.+',
            'description': r'''re:.* today's top stories from the ITV News team.$''',
            'timestamp': int,
            'upload_date': r're:2\d\d\d(?:0[1-9]|1[0-2])(?:[012][1-9]|3[01])',
            'uploader': 'ITVX',
            'thumbnail': r're:https://images\.ctfassets\.net/(?:\w+/)+[\w.]+\.(?:jpg|png)',
            'duration': float,
            'age_limit': None,
        },
        'params': {
            # variable download
            # 'skip_download': True,
        },
        'skip': 'only available in UK',
    }
    ]

    def _og_extract(self, webpage, require_title=False):
        return {
            'title': self._og_search_title(webpage, fatal=require_title),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'uploader': self._og_search_property('site_name', webpage, default=None),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # now quite different params!
        params = extract_attributes(self._search_regex(
            r'''(<[^>]+\b(?:class|data-testid)\s*=\s*("|')genie-container\2[^>]*>)''',
            webpage, 'params'))

        ios_playlist_url = traverse_obj(
            params, 'data-video-id', 'data-video-playlist',
            get_all=False, expected_type=url_or_none)

        headers = self.geo_verification_headers()
        headers.update({
            'Accept': 'application/vnd.itv.vod.playlist.v2+json',
            'Content-Type': 'application/json',
        })
        ios_playlist = self._download_json(
            ios_playlist_url, video_id, data=json.dumps({
                'user': {
                    'entitlements': [],
                },
                'device': {
                    'manufacturer': 'Mobile Safari',
                    'model': '5.1',
                    'os': {
                        'name': 'iOS',
                        'version': '5.0',
                        'type': ' mobile'
                    }
                },
                'client': {
                    'version': '4.1',
                    'id': 'browser',
                    'supportsAdPods': True,
                    'service': 'itv.x',
                    'appversion': '2.43.28',
                },
                'variantAvailability': {
                    'player': 'hls',
                    'featureset': {
                        'min': ['hls', 'aes', 'outband-webvtt'],
                        'max': ['hls', 'aes', 'outband-webvtt']
                    },
                    'platformTag': 'mobile'
                }
            }).encode(), headers=headers)
        video_data = ios_playlist['Playlist']['Video']
        ios_base_url = traverse_obj(video_data, 'Base', expected_type=url_or_none)

        media_url = (
            (lambda u: url_or_none(urljoin(ios_base_url, u)))
            if ios_base_url else url_or_none)

        formats = []
        for media_file in traverse_obj(video_data, 'MediaFiles', expected_type=list) or []:
            href = traverse_obj(media_file, 'Href', expected_type=media_url)
            if not href:
                continue
            ext = determine_ext(href)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    href, video_id, 'mp4', entry_protocol='m3u8',
                    m3u8_id='hls', fatal=False))

            else:
                formats.append({
                    'url': href,
                })
        self._sort_formats(formats)
        for f in formats:
            f.setdefault('http_headers', {})
            f['http_headers'].update(self._vanilla_ua_header())

        subtitles = {}
        for sub in traverse_obj(video_data, 'Subtitles', expected_type=list) or []:
            href = traverse_obj(sub, 'Href', expected_type=url_or_none)
            if not href:
                continue
            subtitles.setdefault('en', []).append({
                'url': href,
                'ext': determine_ext(href, 'vtt'),
            })

        next_data = self._search_nextjs_data(webpage, video_id, fatal=False, default={})
        video_data.update(traverse_obj(next_data, ('props', 'pageProps', ('title', 'episode')), expected_type=dict)[0] or {})
        title = traverse_obj(video_data, 'headerTitle', 'episodeTitle')
        info = self._og_extract(webpage, require_title=not title)
        tn = info.pop('thumbnail', None)
        if tn:
            info['thumbnails'] = [{'url': tn}]

        # num. episode title
        num_ep_title = video_data.get('numberedEpisodeTitle')
        if not num_ep_title:
            num_ep_title = clean_html(get_element_by_attribute('data-testid', 'episode-hero-description-strong', webpage))
            num_ep_title = num_ep_title and num_ep_title.rstrip(' -')
        ep_title = strip_or_none(
            video_data.get('episodeTitle')
            or (num_ep_title.split('.', 1)[-1] if num_ep_title else None))
        title = title or re.sub(r'\s+-\s+ITVX$', '', info['title'])
        if ep_title and ep_title != title:
            title = title + ' - ' + ep_title

        def get_thumbnails():
            tns = []
            for w, x in (traverse_obj(video_data, ('imagePresets'), expected_type=dict) or {}).items():
                if isinstance(x, dict):
                    for y, z in x.items():
                        tns.append({'id': w + '_' + y, 'url': z})
            return tns or None

        video_str = lambda *x: traverse_obj(
            video_data, *x, get_all=False, expected_type=strip_or_none)

        return merge_dicts({
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            # parsing hh:mm:ss:nnn not yet patched
            'duration': parse_duration(re.sub(r'(\d{2})(:)(\d{3}$)', r'\1.\3', video_data.get('Duration') or '')),
            'description': video_str('synopsis'),
            'timestamp': traverse_obj(video_data, 'broadcastDateTime', 'dateTime', expected_type=parse_iso8601),
            'thumbnails': get_thumbnails(),
            'series': video_str('showTitle', 'programmeTitle'),
            'series_number': int_or_none(video_data.get('seriesNumber')),
            'episode': ep_title,
            'episode_number': int_or_none((num_ep_title or '').split('.')[0]),
            'channel': video_str('channel'),
            'categories': traverse_obj(video_data, ('categories', 'formatted'), expected_type=list),
            'age_limit': {False: 16, True: 0}.get(video_data.get('isChildrenCategory')),
        }, info)


class ITVBTCCIE(ITVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?itv\.com/(?!(?:watch|hub)/)(?:[^/]+/)+(?P<id>[^/?#&]+)'
    IE_DESC = 'ITV articles: News, British Touring Car Championship'
    _TESTS = [{
        'note': 'British Touring Car Championship',
        'url': 'https://www.itv.com/btcc/articles/btcc-2018-all-the-action-from-brands-hatch',
        'info_dict': {
            'id': 'btcc-2018-all-the-action-from-brands-hatch',
            'title': 'BTCC 2018: All the action from Brands Hatch',
        },
        'playlist_mincount': 9,
    }, {
        'note': 'redirects to /btcc/articles/...',
        'url': 'http://www.itv.com/btcc/races/btcc-2018-all-the-action-from-brands-hatch',
        'only_matching': True,
    }, {
        'note': 'news article',
        'url': 'https://www.itv.com/news/wales/2020-07-23/sean-fletcher-shows-off-wales-coastline-in-new-itv-series-as-british-tourists-opt-for-staycations',
        'info_dict': {
            'id': 'sean-fletcher-shows-off-wales-coastline-in-new-itv-series-as-british-tourists-opt-for-staycations',
            'title': '''Sean Fletcher on why Wales' coastline should be your 'staycation' destination | ITV News''',
        },
        'playlist_mincount': 1,
    }]

    # should really be a class var of the BC IE
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/%s_default/index.html?videoId=%s'
    BRIGHTCOVE_ACCOUNT = '1582188683001'
    BRIGHTCOVE_PLAYER = 'HkiHLnNRx'

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage, urlh = self._download_webpage_handle(url, playlist_id)
        link = compat_urlparse.urlparse(urlh.geturl()).path.strip('/')

        next_data = self._search_nextjs_data(webpage, playlist_id, fatal=False, default='{}')
        path_prefix = compat_urlparse.urlparse(next_data.get('assetPrefix') or '').path.strip('/')
        link = remove_start(link, path_prefix).strip('/')

        content = traverse_obj(
            next_data, ('props', 'pageProps', Ellipsis),
            expected_type=lambda x: x if x['link'] == link else None,
            get_all=False, default={})
        content = traverse_obj(
            content, ('body', 'content', Ellipsis, 'data'),
            expected_type=lambda x: x if x.get('name') == 'Brightcove' or x.get('type') == 'Brightcove' else None)

        contraband = {
            # ITV does not like some GB IP ranges, so here are some
            # IP blocks it accepts
            'geo_ip_blocks': [
                '193.113.0.0/16', '54.36.162.0/23', '159.65.16.0/21'
            ],
            'referrer': urlh.geturl(),
        }

        def entries():

            for data in content or []:
                video_id = data.get('id')
                if not video_id:
                    continue
                account = data.get('accountId') or self.BRIGHTCOVE_ACCOUNT
                player = data.get('playerId') or self.BRIGHTCOVE_PLAYER
                yield self.url_result(
                    smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % (account, player, video_id), contraband),
                    ie=BrightcoveNewIE.ie_key(), video_id=video_id)

            # obsolete ?
            for video_id in re.findall(r'''data-video-id=["'](\d+)''', webpage):
                yield self.url_result(
                    smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % (self.BRIGHTCOVE_ACCOUNT, self.BRIGHTCOVE_PLAYER, video_id), contraband),
                    ie=BrightcoveNewIE.ie_key(), video_id=video_id)

        title = self._og_search_title(webpage, fatal=False)

        return self.playlist_result(entries(), playlist_id, title)
