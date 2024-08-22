from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse_unquote
)
from ..utils import (
    determine_ext,
    ExtractorError,
    extract_attributes,
    find_xpath_attr,
    get_element_by_attribute,
    get_element_by_class,
    int_or_none,
    js_to_json,
    merge_dicts,
    parse_iso8601,
    smuggle_url,
    str_to_int,
    unescapeHTML,
)
from .senateisvp import SenateISVPIE
from .ustream import UstreamIE


class CSpanIE(InfoExtractor):
    _BASIC_URL = r'https?://(?:www\.)?c-span\.org/'
    _VALID_URL = r'https?://(?:www\.)?c-span\.org/video/\?(?P<id>[0-9a-f]+)'
    IE_DESC = 'C-SPAN'
    _TESTS = [{
        'url': 'http://www.c-span.org/video/?313572-1/HolderonV',
        'md5': '94b29a4f131ff03d23471dd6f60b6a1d',
        'info_dict': {
            'id': '315139',
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
        },
        'playlist_mincount': 2,
        'skip': 'Regularly fails on travis, for unknown reasons',
    }, {
        'url': 'http://www.c-span.org/video/?c4486943/cspan-international-health-care-models',
        # md5 is unstable
        'info_dict': {
            'id': 'c4486943',
            'ext': 'mp4',
            'title': 'CSPAN - International Health Care Models',
            'description': 'md5:7a985a2d595dba00af3d9c9f0783c967',
        }
    }, {
        'url': 'http://www.c-span.org/video/?318608-1/gm-ignition-switch-recall',
        'info_dict': {
            'id': '342759',
            'title': 'General Motors Ignition Switch Recall',
        },
        'playlist_mincount': 6,
    }, {
        # Video from senate.gov
        'url': 'http://www.c-span.org/video/?104517-1/immigration-reforms-needed-protect-skilled-american-workers',
        'info_dict': {
            'id': 'judiciary031715',
            'ext': 'mp4',
            'title': 'Immigration Reforms Needed to Protect Skilled American Workers',
        },
        'params': {
            'skip_download': True,  # m3u8 downloads
        }
    }, {
        # Ustream embedded video
        'url': 'https://www.c-span.org/video/?114917-1/armed-services',
        'info_dict': {
            'id': '58428542',
            'ext': 'flv',
            'title': 'USHR07 Armed Services Committee',
            'description': 'hsas00-2118-20150204-1000et-07\n\n\nUSHR07 Armed Services Committee',
            'timestamp': 1423060374,
            'upload_date': '20150204',
            'uploader': 'HouseCommittee',
            'uploader_id': '12987475',
        },
    }, {
        # Audio Only
        'url': 'https://www.c-span.org/video/?437336-1/judiciary-antitrust-competition-policy-consumer-rights',
        'only_matching': True,
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/%s_%s/index.html?videoId=%s'

    @classmethod
    def is_basic_url(cls, url):
        if '_BASIC_URL_RE' not in cls.__dict__:
            cls._BASIC_URL_RE = re.compile(cls._BASIC_URL)

        return cls._BASIC_URL_RE.match(url) is not None

    @classmethod
    def get_basic_url(cls, url):
        return "/".join(url.rstrip('/').split('/')[:3])

    @classmethod
    def _get_id(cls, url):
        if '_ID_URL_RE' not in cls.__dict__:
            cls._ID_URL_RE = re.compile(cls._ID_URL)

        if cls._ID_URL_RE.match(url) is not None:
            m = cls._ID_URL_RE.match(url)
            assert m
            return compat_str(m.group('id'))
        else:
            return compat_urllib_parse_unquote(os.path.splitext(url.rstrip('/').split('/')[-1])[0])

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_type = None
        webpage = self._download_webpage(url, video_id)

        ustream_url = UstreamIE._extract_url(webpage)
        if ustream_url:
            return self.url_result(ustream_url, UstreamIE.ie_key())

        if '&vod' not in url:
            bc = self._search_regex(
                r"(<[^>]+id='brightcove-player-embed'[^>]+>)",
                webpage, 'brightcove embed', default=None)
            if bc:
                bc_attr = extract_attributes(bc)
                bc_url = self.BRIGHTCOVE_URL_TEMPLATE % (
                    bc_attr.get('data-bcaccountid', '3162030207001'),
                    bc_attr.get('data-noprebcplayerid', 'SyGGpuJy3g'),
                    bc_attr.get('data-newbcplayerid', 'default'),
                    bc_attr['data-bcid'])
                return self.url_result(smuggle_url(bc_url, {'source_url': url}))

        def add_referer(formats):
            for f in formats:
                f.setdefault('http_headers', {})['Referer'] = url

        # As of 01.12.2020 this path looks to cover all cases making the rest
        # of the code unnecessary
        jwsetup = self._parse_json(
            self._search_regex(
                r'(?s)jwsetup\s*=\s*({.+?})\s*;', webpage, 'jwsetup',
                default='{}'),
            video_id, transform_source=js_to_json, fatal=False)
        if jwsetup:
            info = self._parse_jwplayer_data(
                jwsetup, video_id, require_title=False, m3u8_id='hls',
                base_url=url)
            add_referer(info['formats'])
            for subtitles in info['subtitles'].values():
                for subtitle in subtitles:
                    ext = determine_ext(subtitle['url'])
                    if ext == 'php':
                        ext = 'vtt'
                    subtitle['ext'] = ext
            ld_info = self._search_json_ld(webpage, video_id, default={})
            title = get_element_by_class('video-page-title', webpage) or \
                self._og_search_title(webpage)
            description = get_element_by_attribute('itemprop', 'description', webpage) or \
                self._html_search_meta(['og:description', 'description'], webpage)
            return merge_dicts(info, ld_info, {
                'title': title,
                'thumbnail': get_element_by_attribute('itemprop', 'thumbnailUrl', webpage),
                'description': description,
                'timestamp': parse_iso8601(get_element_by_attribute('itemprop', 'uploadDate', webpage)),
                'location': get_element_by_attribute('itemprop', 'contentLocation', webpage),
                'duration': int_or_none(self._search_regex(
                    r'jwsetup\.seclength\s*=\s*(\d+);',
                    webpage, 'duration', fatal=False)),
                'view_count': str_to_int(self._search_regex(
                    r"<span[^>]+class='views'[^>]*>([\d,]+)\s+Views</span>",
                    webpage, 'views', fatal=False)),
            })

        # Obsolete
        # We first look for clipid, because clipprog always appears before
        patterns = [r'id=\'clip(%s)\'\s*value=\'([0-9]+)\'' % t for t in ('id', 'prog')]
        results = list(filter(None, (re.search(p, webpage) for p in patterns)))
        if results:
            matches = results[0]
            video_type, video_id = matches.groups()
            video_type = 'clip' if video_type == 'id' else 'program'
        else:
            m = re.search(r'data-(?P<type>clip|prog)id=["\'](?P<id>\d+)', webpage)
            if m:
                video_id = m.group('id')
                video_type = 'program' if m.group('type') == 'prog' else 'clip'
            else:
                senate_isvp_url = SenateISVPIE._search_iframe_url(webpage)
                if senate_isvp_url:
                    title = self._og_search_title(webpage)
                    surl = smuggle_url(senate_isvp_url, {'force_title': title})
                    return self.url_result(surl, 'SenateISVP', video_id, title)
                video_id = self._search_regex(
                    r'jwsetup\.clipprog\s*=\s*(\d+);',
                    webpage, 'jwsetup program id', default=None)
                if video_id:
                    video_type = 'program'
        if video_type is None or video_id is None:
            error_message = get_element_by_class('VLplayer-error-message', webpage)
            if error_message:
                raise ExtractorError(error_message)
            raise ExtractorError('unable to find video id and type')

        def get_text_attr(d, attr):
            return d.get(attr, {}).get('#text')

        data = self._download_json(
            'http://www.c-span.org/assets/player/ajax-player.php?os=android&html5=%s&id=%s' % (video_type, video_id),
            video_id)['video']
        if data['@status'] != 'Success':
            raise ExtractorError('%s said: %s' % (self.IE_NAME, get_text_attr(data, 'error')), expected=True)

        doc = self._download_xml(
            'http://www.c-span.org/common/services/flashXml.php?%sid=%s' % (video_type, video_id),
            video_id)

        description = self._html_search_meta('description', webpage)

        title = find_xpath_attr(doc, './/string', 'name', 'title').text
        thumbnail = find_xpath_attr(doc, './/string', 'name', 'poster').text

        files = data['files']
        capfile = get_text_attr(data, 'capfile')

        entries = []
        for partnum, f in enumerate(files):
            formats = []
            for quality in f.get('qualities', []):
                formats.append({
                    'format_id': '%s-%sp' % (get_text_attr(quality, 'bitrate'), get_text_attr(quality, 'height')),
                    'url': unescapeHTML(get_text_attr(quality, 'file')),
                    'height': int_or_none(get_text_attr(quality, 'height')),
                    'tbr': int_or_none(get_text_attr(quality, 'bitrate')),
                })
            if not formats:
                path = unescapeHTML(get_text_attr(f, 'path'))
                if not path:
                    continue
                formats = self._extract_m3u8_formats(
                    path, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls') if determine_ext(path) == 'm3u8' else [{'url': path, }]
            add_referer(formats)
            self._sort_formats(formats)
            entries.append({
                'id': '%s_%d' % (video_id, partnum + 1),
                'title': (
                    title if len(files) == 1 else
                    '%s part %d' % (title, partnum + 1)),
                'formats': formats,
                'description': description,
                'thumbnail': thumbnail,
                'duration': int_or_none(get_text_attr(f, 'length')),
                'subtitles': {
                    'en': [{
                        'url': capfile,
                        'ext': determine_ext(capfile, 'dfxp')
                    }],
                } if capfile else None,
            })

        if len(entries) == 1:
            entry = dict(entries[0])
            entry['id'] = 'c' + video_id if video_type == 'clip' else video_id
            return entry
        else:
            return {
                '_type': 'playlist',
                'entries': entries,
                'title': title,
                'id': 'c' + video_id if video_type == 'clip' else video_id,
            }
