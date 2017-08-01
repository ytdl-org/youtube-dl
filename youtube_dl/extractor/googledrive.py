from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    lowercase_escape,
    error_to_compat_str,
    update_url_query,
)


class GoogleDriveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)|video\.google\.com/get_player\?.*?docid=)(?P<id>[a-zA-Z0-9_-]{28,})'
    _TESTS = [{
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'md5': 'd109872761f7e7ecf353fa108c0dbe1e',
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
            'duration': 45,
        }
    }, {
        # video id is longer than 28 characters
        'url': 'https://drive.google.com/file/d/1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ/edit',
        'md5': 'c230c67252874fddd8170e3fd1a45886',
        'info_dict': {
            'id': '1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ',
            'ext': 'mp4',
            'title': 'Andreea Banica feat Smiley - Hooky Song (Official Video).mp4',
            'duration': 189,
        },
        'only_matching': True
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
    _CAPTION_FORMATS_EXT = []
    _CAPTIONS_BY_COUNTRY_XML = None

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28,})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _set_captions_data(self, video_id, video_subtitles_id, hl):
        try:
            self._CAPTIONS_BY_COUNTRY_XML = self._download_xml(
                'https://drive.google.com/timedtext?id=%s&vid=%s&hl=%s&type=list&tlangs=1&v=%s&fmts=1&vssids=1', video_id, query={
                    'id': video_id,
                    'vid': video_subtitles_id,
                    'hl': hl,
                    'v': video_id,
                })
        except ExtractorError as ee:
            self.report_warning('unable to download video subtitles: %s' % error_to_compat_str(ee))
        if self._CAPTIONS_BY_COUNTRY_XML is not None:
            caption_available_extensions = self._CAPTIONS_BY_COUNTRY_XML.findall('format')
            for caption_extension in caption_available_extensions:
                if caption_extension.attrib.get('fmt_code') and not caption_extension.attrib.get('default'):
                    self._CAPTION_FORMATS_EXT.append(caption_extension.attrib['fmt_code'])

    def _get_subtitles(self, video_id, video_subtitles_id, hl):
        if not video_subtitles_id or not hl:
            return None
        if self._CAPTIONS_BY_COUNTRY_XML is None:
            self._set_captions_data(video_id, video_subtitles_id, hl)
            if self._CAPTIONS_BY_COUNTRY_XML is None:
                return None

        subtitles = {}
        subtitle_available_tracks = self._CAPTIONS_BY_COUNTRY_XML.findall('track')
        for subtitle_track in subtitle_available_tracks:
            if not subtitle_track.attrib.get('lang_code'):
                continue
            subtitle_lang_code = subtitle_track.attrib['lang_code']
            subtitle_format_data = []
            for subtitle_format in self._CAPTION_FORMATS_EXT:
                query = {
                    'vid': video_subtitles_id,
                    'v': video_id,
                    'lang': subtitle_lang_code,
                    'fmt': subtitle_format,
                    'name': '',
                    'kind': '',
                }
                subtitle_format_data.append({
                    'url': update_url_query('https://drive.google.com/timedtext?vid=%s&v=%s&type=track&lang=%s&name&kind&fmt=%s', query),
                    'ext': subtitle_format,
                })
            subtitles[subtitle_lang_code] = subtitle_format_data
        if not subtitles:
            self.report_warning('video doesn\'t have subtitles')
        return subtitles

    def _get_automatic_captions(self, video_id, video_subtitles_id, hl):
        if not video_subtitles_id or not hl:
            return None
        if self._CAPTIONS_BY_COUNTRY_XML is None:
            self._set_captions_data(video_id, video_subtitles_id, hl)
            if self._CAPTIONS_BY_COUNTRY_XML is None:
                return None
        self.to_screen('%s: Looking for automatic captions' % video_id)

        subtitle_original_track = self._CAPTIONS_BY_COUNTRY_XML.find('track')
        if subtitle_original_track is None:
            return None
        if not subtitle_original_track.attrib.get('lang_code'):
            return None
        subtitle_original_lang_code = subtitle_original_track.attrib['lang_code']

        automatic_captions = {}
        automatic_caption_available_targets = self._CAPTIONS_BY_COUNTRY_XML.findall('target')
        for automatic_caption_target in automatic_caption_available_targets:
            if not automatic_caption_target.attrib.get('lang_code'):
                continue
            automatic_caption_lang_code = automatic_caption_target.attrib['lang_code']
            automatic_caption_format_data = []
            for automatic_caption_format in self._CAPTION_FORMATS_EXT:
                query = {
                    'vid': video_subtitles_id,
                    'v': video_id,
                    'lang': subtitle_original_lang_code,
                    'fmt': automatic_caption_format,
                    'tlang': automatic_caption_lang_code,
                    'name': '',
                    'kind': '',
                }
                automatic_caption_format_data.append({
                    'url': update_url_query('https://drive.google.com/timedtext?vid=%s&v=%s&type=track&lang=%s&name&kind&fmt=%s&tlang=%s', query),
                    'ext': automatic_caption_format,
                })
            automatic_captions[automatic_caption_lang_code] = automatic_caption_format_data
        if not automatic_captions:
            self.report_warning('video doesn\'t have automatic captions')
        return automatic_captions

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://docs.google.com/file/d/%s' % video_id, video_id)

        reason = self._search_regex(r'"reason"\s*,\s*"([^"]+)', webpage, 'reason', default=None)
        if reason:
            raise ExtractorError(reason)

        title = self._search_regex(r'"title"\s*,\s*"([^"]+)', webpage, 'title')
        duration = int_or_none(self._search_regex(
            r'"length_seconds"\s*,\s*"([^"]+)', webpage, 'length seconds', default=None))
        fmt_stream_map = self._search_regex(
            r'"fmt_stream_map"\s*,\s*"([^"]+)', webpage, 'fmt stream map').split(',')
        fmt_list = self._search_regex(r'"fmt_list"\s*,\s*"([^"]+)', webpage, 'fmt_list').split(',')

        resolutions = {}
        for fmt in fmt_list:
            mobj = re.search(
                r'^(?P<format_id>\d+)/(?P<width>\d+)[xX](?P<height>\d+)', fmt)
            if mobj:
                resolutions[mobj.group('format_id')] = (
                    int(mobj.group('width')), int(mobj.group('height')))

        formats = []
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
        self._sort_formats(formats)

        hl = self._search_regex(
            r'"hl"\s*,\s*"([^"]+)', webpage, 'hl', default=None)
        video_subtitles_id = None
        ttsurl = self._search_regex(
            r'"ttsurl"\s*,\s*"([^"]+)', webpage, 'ttsurl', default=None)
        if ttsurl:
            # the video Id for subtitles will be the last value in the ttsurl query string
            video_subtitles_id = ttsurl.encode('utf-8').decode('unicode_escape').split('=')[-1]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, video_subtitles_id, hl),
            'automatic_captions': self.extract_automatic_captions(video_id, video_subtitles_id, hl),
        }
