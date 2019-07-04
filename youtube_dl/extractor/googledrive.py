from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    lowercase_escape,
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
        'md5': 'bfbd670d03a470bb1e6d4a257adec12e',
        'info_dict': {
            'id': '0B-vUyvmDLdWDcEt4WjBqcmI2XzQ',
            'ext': 'mp4',
            'title': 'Annabelle Creation (2017)- Z.V1 [TH].MP4',
        }
    }, {
        # video id is longer than 28 characters
        'url': 'https://drive.google.com/file/d/1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ/edit',
        'info_dict': {
            'id': '1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ',
            'ext': 'mp4',
            'title': 'Andreea Banica feat Smiley - Hooky Song (Official Video).mp4',
            'duration': 189,
        },
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
        webpage = self._download_webpage(
            'http://docs.google.com/file/d/%s' % video_id, video_id)

        title = self._search_regex(
            r'"title"\s*,\s*"([^"]+)', webpage, 'title',
            default=None) or self._og_search_title(webpage)
        duration = int_or_none(self._search_regex(
            r'"length_seconds"\s*,\s*"([^"]+)', webpage, 'length seconds',
            default=None))

        formats = []
        fmt_stream_map = self._search_regex(
            r'"fmt_stream_map"\s*,\s*"([^"]+)', webpage,
            'fmt stream map', default='').split(',')
        fmt_list = self._search_regex(
            r'"fmt_list"\s*,\s*"([^"]+)', webpage,
            'fmt_list', default='').split(',')
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
        urlh = self._request_webpage(
            source_url, video_id, note='Requesting source file',
            errnote='Unable to request source file', fatal=False)
        if urlh:
            def add_source_format(src_url):
                formats.append({
                    'url': src_url,
                    'ext': determine_ext(title, 'mp4').lower(),
                    'format_id': 'source',
                    'quality': 1,
                })
            if urlh.headers.get('Content-Disposition'):
                add_source_format(source_url)
            else:
                confirmation_webpage = self._webpage_read_content(
                    urlh, url, video_id, note='Downloading confirmation page',
                    errnote='Unable to confirm download', fatal=False)
                if confirmation_webpage:
                    confirm = self._search_regex(
                        r'confirm=([^&"\']+)', confirmation_webpage,
                        'confirmation code', fatal=False)
                    if confirm:
                        add_source_format(update_url_query(source_url, {
                            'confirm': confirm,
                        }))

        if not formats:
            reason = self._search_regex(
                r'"reason"\s*,\s*"([^"]+)', webpage, 'reason', default=None)
            if reason:
                raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        hl = self._search_regex(
            r'"hl"\s*,\s*"([^"]+)', webpage, 'hl', default=None)
        subtitles_id = None
        ttsurl = self._search_regex(
            r'"ttsurl"\s*,\s*"([^"]+)', webpage, 'ttsurl', default=None)
        if ttsurl:
            # the video Id for subtitles will be the last value in the ttsurl
            # query string
            subtitles_id = ttsurl.encode('utf-8').decode(
                'unicode_escape').split('=')[-1]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, subtitles_id, hl),
            'automatic_captions': self.extract_automatic_captions(
                video_id, subtitles_id, hl),
        }
