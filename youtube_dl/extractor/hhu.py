# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json, RegexNotFoundError, urljoin

import json
import re


class HHUIE(InfoExtractor):
    _VALID_URL = r'https://mediathek\.hhu\.de/watch/(?P<id>.+)'
    _TEST = {
        'url': 'https://mediathek.hhu.de/watch/2dd05982-ea45-4108-9620-0c36e6ed8df5',
        'md5': 'b99ff77f2148b1e754555abdf53f0e51',
        'info_dict': {
            'id': '2dd05982-ea45-4108-9620-0c36e6ed8df5',
            'ext': 'mp4',
            'title': 'Das Multimediazentrum',
            'description': '',
            'uploader_id': 'clames',
            'thumbnail': 'https://mediathek.hhu.de/thumbs/2dd05982-ea45-4108-9620-0c36e6ed8df5/thumb_000.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, webpage_url = self._download_webpage_handle(url, video_id)
        if webpage_url.geturl().startswith("https://sts."):
            self.raise_login_required()
            # Some videos need a login, maybe TODO.
        try:
            config_js = self._search_regex(
                r'playerInstance\.setup\(([^;]+)\);', webpage, 'config_js'
            )
            # remove 'link: encodeURI("<our url>"),'
            if 'link: encodeURI' in config_js:
                encode_begin = config_js.find('link: encodeURI')
                encode_end = config_js.find(')', encode_begin)
                config_js = (
                    config_js[:encode_begin] + config_js[encode_end + 2:]
                )
                del encode_begin, encode_end
            config = json.loads(js_to_json(config_js))
            if len(config['playlist']) > 1:
                self.report_warning(
                    'more than one video, just taking the first one'
                )
            video = config['playlist'][0]
            formats = [
                {
                    'url': urljoin('https://mediathek.hhu.de/', source['file']),
                    'format_note': source.get('label'),
                    'format_id': source['file'].split("/")[-1],
                }
                for source in video['sources']
            ]
            formats.reverse()  # config sorts from highest to lowest quality
            title = video.get('title')
            thumbnail = video.get('image')
            thumbnail = urljoin('https://mediathek.hhu.de/', thumbnail) if thumbnail else None

        except (RegexNotFoundError, ValueError):
            self.report_warning('failed to get player config, guessing formats')
            # This will likely work but better warn.
            file_id = self._html_search_regex(
                r"{ file: '\/movies\/(.+?)\/v_100\.mp4', label: '",
                webpage, 'file_id'
            )
            formats = [
                ({'url': format_url.format(file_id)})
                for format_url in (
                    'https://mediathek.hhu.de/movies/{}/v_10.webm',
                    'https://mediathek.hhu.de/movies/{}/v_10.mp4',
                    'https://mediathek.hhu.de/movies/{}/v_50.webm',
                    'https://mediathek.hhu.de/movies/{}/v_50.mp4',
                    'https://mediathek.hhu.de/movies/{}/v_100.webm',
                    'https://mediathek.hhu.de/movies/{}/v_100.mp4',
                )
            ]
            title = thumbnail = None
        if not title:
            title = self._html_search_regex(
                r'<h1 id="mt_watch-headline-title">\s+(.+?)\s+<\/h1>',
                webpage, 'title'
            )
        if not title:
            title = self._og_search_title(webpage, fatal=False)
        description = self._html_search_regex(
            r'<p id="mt_watch-description" class="watch-description">\s+(.+?)\s+<\/p>',
            webpage, 'description', fatal=False
        )
        if not description:
            description = self._og_search_description(webpage, default='')
        if not thumbnail:
            thumbnail = self._og_search_property(
                'image:secure_url', webpage, 'thumbnail', fatal=False
            )
        uploader = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href=".+">(.+?)<\/a>',
            webpage, 'uploader', fatal=False
        )


        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'formats': formats,
        }
