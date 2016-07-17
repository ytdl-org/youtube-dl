# coding: utf-8
from __future__ import unicode_literals

import datetime
import os

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
    strip_bom_utf8,
    RegexNotFoundError,
    UnavailableVideoError,
    update_url_query,
)

class CBAIE(InfoExtractor):
    IE_NAME = 'cba'
    IE_DESC = 'cultural broadcasting archive'
    _VALID_URL = r'https?://(?:www\.)?cba\.fro\.at/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://cba.fro.at/320619',
        'md5': 'e40379688fcc5e95d6d8a482bb665b02',
        'info_dict': {
            'id': '320619',
            'ext': 'mp3',
            'title': 'Radio Netwatcher Classics vom 15.7.2016 – Peter Pilz, Sicherheitssprecher Grüne über die nationale Entwicklung zum Überwachungsstaat',
            'url': 'https://cba.fro.at/wp-content/uploads/radio_netwatcher/netwatcher-20160715.mp3',
        }
    }
    _FORMATS = {
        'audio/ogg': {'id': '1', 'ext': 'ogg', 'preference': 100},
        'audio/mpeg': {'id': '2', 'ext': 'mp3', 'preference': 50}
    }
    _API_KEY = None

    def __init__(self, *args, **kwargs):
        try:
            self._API_KEY = os.environ["CBA_API_KEY"]
        except KeyError:
            pass

    def _add_optional_parameter(self, formats, name, data, key, convert=None):
        try:
            param = data[key]
            if convert:
                param = convert(param)
            formats[name] = param
        except KeyError:
            pass

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_posts_url = "https://cba.fro.at/wp-json/wp/v2/posts/%s" % video_id
        api_media_url = "https://cba.fro.at/wp-json/wp/v2/media?media_type=audio&parent=%s" % video_id

        title = 'unknown'
        description = ''
        formats = []

        posts_result = self._download_json(api_posts_url, video_id, 'query posts api-endpoint',
                                           'unable to query posts api-endpoint', transform_source=strip_bom_utf8)
        try:
            title = clean_html(posts_result['title']['rendered'])
            description = clean_html(posts_result['content']['rendered'])
        except KeyError:
            pass

        api_key_str = " (without API_KEY)"
        if self._API_KEY:
            api_key_str =  " (using API_KEY '%s')" % self._API_KEY
            api_media_url = update_url_query(api_media_url, {'c': self._API_KEY})

        media_result = self._download_json(api_media_url, video_id, 'query media api-endpoint%s' % api_key_str,
                                         'unable to qeury media api-endpoint%s' % api_key_str, transform_source=strip_bom_utf8)
        for media in media_result:
            try:
                url = media['source_url']
                if url == "":
                    continue

                ft = media['mime_type']
                f = { 'url': url, 'format': ft, 'format_id': self._FORMATS[ft]['id'], 'preference': self._FORMATS[ft]['preference'] }
                self._add_optional_parameter(f, 'filesize', media['media_details'], 'filesize')
                self._add_optional_parameter(f, 'abr', media['media_details'], 'bitrate', lambda x: x/1000)
                self._add_optional_parameter(f, 'asr', media['media_details'], 'sample_rate')

                formats.append(f)
            except KeyError:
                pass

        if len(formats) == 0:
            if self._API_KEY:
                raise ExtractorError('unable to fetch CBA entry')
            else:
                raise UnavailableVideoError('you may need an API key to download copyright protected files')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
