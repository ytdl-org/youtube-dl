# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    mimetype2ext,
    parse_codecs,
    xpath_element,
    xpath_text,
)


class VideaIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        videa(?:kid)?\.hu/
                        (?:
                            videok/(?:[^/]+/)*[^?#&]+-|
                            player\?.*?\bv=|
                            player/v/
                        )
                        (?P<id>[^?#&]+)
                    '''
    _TESTS = [{
        'url': 'http://videa.hu/videok/allatok/az-orult-kigyasz-285-kigyot-kigyo-8YfIAjxwWGwT8HVQ',
        'md5': '97a7af41faeaffd9f1fc864a7c7e7603',
        'info_dict': {
            'id': '8YfIAjxwWGwT8HVQ',
            'ext': 'mp4',
            'title': 'Az őrült kígyász 285 kígyót enged szabadon',
            'thumbnail': r're:^https?://.*',
            'duration': 21,
        },
    }, {
        'url': 'http://videa.hu/videok/origo/jarmuvek/supercars-elozes-jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }, {
        'url': 'http://videa.hu/player?v=8YfIAjxwWGwT8HVQ',
        'only_matching': True,
    }, {
        'url': 'http://videa.hu/player/v/8YfIAjxwWGwT8HVQ?autoplay=1',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/videok/origo/jarmuvek/supercars-elozes-jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/player?v=8YfIAjxwWGwT8HVQ',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/player/v/8YfIAjxwWGwT8HVQ?autoplay=1',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//videa\.hu/player\?.*?\bv=.+?)\1',
            webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_xml(
            'http://videa.hu/videaplayer_get_xml.php', video_id,
            query={'v': video_id})

        video = xpath_element(info, './/video', 'video', fatal=True)
        sources = xpath_element(info, './/video_sources', 'sources', fatal=True)

        title = xpath_text(video, './title', fatal=True)

        formats = []
        for source in sources.findall('./video_source'):
            source_url = source.text
            if not source_url:
                continue
            f = parse_codecs(source.get('codecs'))
            f.update({
                'url': source_url,
                'ext': mimetype2ext(source.get('mimetype')) or 'mp4',
                'format_id': source.get('name'),
                'width': int_or_none(source.get('width')),
                'height': int_or_none(source.get('height')),
            })
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = xpath_text(video, './poster_src')
        duration = int_or_none(xpath_text(video, './duration'))

        age_limit = None
        is_adult = xpath_text(video, './is_adult_content', default=None)
        if is_adult:
            age_limit = 18 if is_adult == '1' else 0

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }
