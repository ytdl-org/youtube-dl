# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    parse_iso8601,
    xpath_text,
)


class NerdistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nerdist\.com/vepisode/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.nerdist.com/vepisode/exclusive-which-dc-characters-w',
        'md5': '3698ed582931b90d9e81e02e26e89f23',
        'info_dict': {
            'display_id': 'exclusive-which-dc-characters-w',
            'id': 'RPHpvJyr',
            'ext': 'mp4',
            'title': 'Your TEEN TITANS Revealed! Who\'s on the show?',
            'thumbnail': 're:^https?://.*/thumbs/.*\.jpg$',
            'description': 'Exclusive: Find out which DC Comics superheroes will star in TEEN TITANS Live-Action TV Show on Nerdist News with Jessica Chobot!',
            'uploader': 'Eric Diaz',
            'upload_date': '20150202',
            'timestamp': 1422892808,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'''(?x)<script\s+(?:type="text/javascript"\s+)?
                src="https?://content\.nerdist\.com/players/([a-zA-Z0-9_]+)-''',
            webpage, 'video ID')
        timestamp = parse_iso8601(self._html_search_meta(
            'shareaholic:article_published_time', webpage, 'upload date'))
        uploader = self._html_search_meta(
            'shareaholic:article_author_name', webpage, 'article author')

        doc = self._download_xml(
            'http://content.nerdist.com/jw6/%s.xml' % video_id, video_id)
        video_info = doc.find('.//item')
        title = xpath_text(video_info, './title', fatal=True)
        description = xpath_text(video_info, './description')
        thumbnail = xpath_text(
            video_info, './{http://rss.jwpcdn.com/}image', 'thumbnail')

        formats = []
        for source in video_info.findall('./{http://rss.jwpcdn.com/}source'):
            vurl = source.attrib['file']
            ext = determine_ext(vurl)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id, entry_protocol='m3u8_native', ext='mp4',
                    preference=0))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    vurl, video_id, fatal=False
                ))
            else:
                formats.append({
                    'format_id': ext,
                    'url': vurl,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'formats': formats,
            'uploader': uploader,
        }
