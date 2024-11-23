from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_parse_qs
from ..utils import (
    determine_ext,
    ExtractorError,
    get_element_by_class,
    int_or_none,
    lowercase_escape,
    try_get,
    update_url_query,
)


class GoogleDriveIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                (?:docs|drive)\.google\.com/
                                (?:
                                    (?:uc|open)\?.*?id=|
                                    file/d/
                                )|
                                video\.google\.com/get_player\?.*?docid=
                            )
                            (?P<id>[a-zA-Z0-9_-]{28,})
                    '''
    _TESTS = [{
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'md5': '5c602afbbf2c1db91831f5d82f678554',
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
            'duration': 45,
        }
    }, {
        # video can't be watched anonymously due to view count limit reached,
        # but can be downloaded (see https://github.com/ytdl-org/youtube-dl/issues/14046)
        'url': 'https://drive.google.com/file/d/0B-vUyvmDLdWDcEt4WjBqcmI2XzQ/view',
        'only_matching': True,
    }, {
        # video id is longer than 28 characters
        'url': 'https://drive.google.com/file/d/1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ/edit',
        'only_matching': True,
    }, {
        'url': 'https://drive.google.com/open?id=0B2fjwgkl1A_CX083Tkowdmt6d28',
        'only_matching': True,
    }, {
        'url': 'https://drive.google.com/uc?id=0B2fjwgkl1A_CX083Tkowdmt6d28',
        'only_matching': True,
    }]
    _FORMATS_EXT = {
        '5': 'flv',
        '6': 'flv',
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '34': 'flv',
        '35': 'flv',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',
        '59': 'mp4',
    }
    _BASE_URL_CAPTIONS = 'https://drive.google.com/timedtext'
    _CAPTIONS_ENTRY_TAG = {
        'subtitles': 'track',
        'automatic_captions': 'target',
    }
    _caption_formats_ext = []
    _captions_xml = None

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28,})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _download_subtitles_xml(self, video_id, subtitles_id, hl):
        if self._captions_xml:
            return
        self._captions_xml = self._download_xml(
            self._BASE_URL_CAPTIONS, video_id, query={
                'id': video_id,
                'vid': subtitles_id,
                'hl': hl,
                'v': video_id,
                'type': 'list',
                'tlangs': '1',
                'fmts': '1',
                'vssids': '1',
            }, note='Downloading subtitles XML',
            errnote='Unable to download subtitles XML', fatal=False)
        if self._captions_xml:
            for f in self._captions_xml.findall('format'):
                if f.attrib.get('fmt_code') and not f.attrib.get('default'):
                    self._caption_formats_ext.append(f.attrib['fmt_code'])

    def _get_captions_by_type(self, video_id, subtitles_id, caption_type,
                              origin_lang_code=None):
        if not subtitles_id or not caption_type:
            return
        captions = {}
        for caption_entry in self._captions_xml.findall(
                self._CAPTIONS_ENTRY_TAG[caption_type]):
            caption_lang_code = caption_entry.attrib.get('lang_code')
            if not caption_lang_code:
                continue
            caption_format_data = []
            for caption_format in self._caption_formats_ext:
                query = {
                    'vid': subtitles_id,
                    'v': video_id,
                    'fmt': caption_format,
                    'lang': (caption_lang_code if origin_lang_code is None
                             else origin_lang_code),
                    'type': 'track',
                    'name': '',
                    'kind': '',
                }
                if origin_lang_code is not None:
                    query.update({'tlang': caption_lang_code})
                caption_format_data.append({
                    'url': update_url_query(self._BASE_URL_CAPTIONS, query),
                    'ext': caption_format,
                })
            captions[caption_lang_code] = caption_format_data
        return captions

    def _get_subtitles(self, video_id, subtitles_id, hl):
        if not subtitles_id or not hl:
            return
        self._download_subtitles_xml(video_id, subtitles_id, hl)
        if not self._captions_xml:
            return
        return self._get_captions_by_type(video_id, subtitles_id, 'subtitles')

    def _get_automatic_captions(self, video_id, subtitles_id, hl):
        if not subtitles_id or not hl:
            return
        self._download_subtitles_xml(video_id, subtitles_id, hl)
        if not self._captions_xml:
            return
        track = self._captions_xml.find('track')
        if track is None:
            return
        origin_lang_code = track.attrib.get('lang_code')
        if not origin_lang_code:
            return
        return self._get_captions_by_type(
            video_id, subtitles_id, 'automatic_captions', origin_lang_code)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = compat_parse_qs(self._download_webpage(
            'https://drive.google.com/get_video_info',
            video_id, query={'docid': video_id}))

        def get_value(key):
            return try_get(video_info, lambda x: x[key][0])

        reason = get_value('reason')
        title = get_value('title')
        if not title and reason:
            raise ExtractorError(reason, expected=True)

        formats = []
        fmt_stream_map = (get_value('fmt_stream_map') or '').split(',')
        fmt_list = (get_value('fmt_list') or '').split(',')
        if fmt_stream_map and fmt_list:
            resolutions = {}
            for fmt in fmt_list:
                mobj = re.search(
                    r'^(?P<format_id>\d+)/(?P<width>\d+)[xX](?P<height>\d+)', fmt)
                if mobj:
                    resolutions[mobj.group('format_id')] = (
                        int(mobj.group('width')), int(mobj.group('height')))

            for fmt_stream in fmt_stream_map:
                fmt_stream_split = fmt_stream.split('|')
                if len(fmt_stream_split) < 2:
                    continue
                format_id, format_url = fmt_stream_split[:2]
                f = {
                    'url': lowercase_escape(format_url),
                    'format_id': format_id,
                    'ext': self._FORMATS_EXT[format_id],
                }
                resolution = resolutions.get(format_id)
                if resolution:
                    f.update({
                        'width': resolution[0],
                        'height': resolution[1],
                    })
                formats.append(f)

        source_url = update_url_query(
            'https://drive.google.com/uc', {
                'id': video_id,
                'export': 'download',
            })

        def request_source_file(source_url, kind):
            return self._request_webpage(
                source_url, video_id, note='Requesting %s file' % kind,
                errnote='Unable to request %s file' % kind, fatal=False)
        urlh = request_source_file(source_url, 'source')
        if urlh:
            def add_source_format(urlh):
                formats.append({
                    # Use redirect URLs as download URLs in order to calculate
                    # correct cookies in _calc_cookies.
                    # Using original URLs may result in redirect loop due to
                    # google.com's cookies mistakenly used for googleusercontent.com
                    # redirect URLs (see #23919).
                    'url': urlh.geturl(),
                    'ext': determine_ext(title, 'mp4').lower(),
                    'format_id': 'source',
                    'quality': 1,
                })
            if urlh.headers.get('Content-Disposition'):
                add_source_format(urlh)
            else:
                confirmation_webpage = self._webpage_read_content(
                    urlh, url, video_id, note='Downloading confirmation page',
                    errnote='Unable to confirm download', fatal=False)
                if confirmation_webpage:
                    confirm = self._search_regex(
                        r'confirm=([^&"\']+)', confirmation_webpage,
                        'confirmation code', default=None)
                    if confirm:
                        confirmed_source_url = update_url_query(source_url, {
                            'confirm': confirm,
                        })
                        urlh = request_source_file(confirmed_source_url, 'confirmed source')
                        if urlh and urlh.headers.get('Content-Disposition'):
                            add_source_format(urlh)
                    else:
                        self.report_warning(
                            get_element_by_class('uc-error-subcaption', confirmation_webpage)
                            or get_element_by_class('uc-error-caption', confirmation_webpage)
                            or 'unable to extract confirmation code')

        if not formats and reason:
            raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        hl = get_value('hl')
        subtitles_id = None
        ttsurl = get_value('ttsurl')
        if ttsurl:
            # the video Id for subtitles will be the last value in the ttsurl
            # query string
            subtitles_id = ttsurl.encode('utf-8').decode(
                'unicode_escape').split('=')[-1]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': 'https://drive.google.com/thumbnail?id=' + video_id,
            'duration': int_or_none(get_value('length_seconds')),
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, subtitles_id, hl),
            'automatic_captions': self.extract_automatic_captions(
                video_id, subtitles_id, hl),
        }
