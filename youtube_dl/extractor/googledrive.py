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
    _BASE_URL_CAPTIONS = 'https://drive.google.com/timedtext'
    _CAPTIONS_ENTRY_TAG = {
        'subtitles': 'track',
        'automatic_captions': 'target',
    }
    _caption_formats_ext = []
    _captions_by_country_xml = None

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28,})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _set_captions_data(self, video_id, video_subtitles_id, hl):
        try:
            self._captions_by_country_xml = self._download_xml(self._BASE_URL_CAPTIONS, video_id, query={
                'id': video_id,
                'vid': video_subtitles_id,
                'hl': hl,
                'v': video_id,
                'type': 'list',
                'tlangs': '1',
                'fmts': '1',
                'vssids': '1',
            })
        except ExtractorError as ee:
            self.report_warning('unable to download video subtitles: %s' % error_to_compat_str(ee))
        if self._captions_by_country_xml is not None:
            caption_available_extensions = self._captions_by_country_xml.findall('format')
            for caption_extension in caption_available_extensions:
                if caption_extension.attrib.get('fmt_code') and not caption_extension.attrib.get('default'):
                    self._caption_formats_ext.append(caption_extension.attrib['fmt_code'])

    def _get_captions_by_type(self, video_id, video_subtitles_id, caption_type, caption_original_lang_code=None):
        if not video_subtitles_id or not caption_type:
            return None
        captions = {}
        for caption_entry in self._captions_by_country_xml.findall(self._CAPTIONS_ENTRY_TAG[caption_type]):
            caption_lang_code = caption_entry.attrib.get('lang_code')
            if not caption_lang_code:
                continue
            caption_format_data = []
            for caption_format in self._caption_formats_ext:
                query = {
                    'vid': video_subtitles_id,
                    'v': video_id,
                    'fmt': caption_format,
                    'lang': caption_lang_code if caption_original_lang_code is None else caption_original_lang_code,
                    'type': 'track',
                    'name': '',
                    'kind': '',
                }
                if caption_original_lang_code is not None:
                    query.update({'tlang': caption_lang_code})
                caption_format_data.append({
                    'url': update_url_query(self._BASE_URL_CAPTIONS, query),
                    'ext': caption_format,
                })
            captions[caption_lang_code] = caption_format_data
        if not captions:
            self.report_warning('video doesn\'t have %s' % caption_type.replace('_', ' '))
        return captions

    def _get_subtitles(self, video_id, video_subtitles_id, hl):
        if not video_subtitles_id or not hl:
            return None
        if self._captions_by_country_xml is None:
            self._set_captions_data(video_id, video_subtitles_id, hl)
            if self._captions_by_country_xml is None:
                return None
        return self._get_captions_by_type(video_id, video_subtitles_id, 'subtitles')

    def _get_automatic_captions(self, video_id, video_subtitles_id, hl):
        if not video_subtitles_id or not hl:
            return None
        if self._captions_by_country_xml is None:
            self._set_captions_data(video_id, video_subtitles_id, hl)
            if self._captions_by_country_xml is None:
                return None
        self.to_screen('%s: Looking for automatic captions' % video_id)
        subtitle_original_track = self._captions_by_country_xml.find('track')
        if subtitle_original_track is None:
            return None
        subtitle_original_lang_code = subtitle_original_track.attrib.get('lang_code')
        if not subtitle_original_lang_code:
            return None
        return self._get_captions_by_type(video_id, video_subtitles_id, 'automatic_captions', subtitle_original_lang_code)

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
