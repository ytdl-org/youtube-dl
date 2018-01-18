# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


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
        # TODO: Login for some videos.
        video_id = self._match_id(url)
        webpage, webpage_url = self._download_webpage_handle(url, video_id)
        if webpage_url.geturl().startswith("https://sts."):
            self.raise_login_required()
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
        try:
            title = self._og_search_title(webpage)
        except:
            title = self._html_search_regex(
                r'<h1 id="mt_watch-headline-title">\s+(.+?)\s+<\/h1>',
                webpage, 'title'
            )
        try:
            description = self._og_search_description(webpage)
        except:
            description = self._html_search_regex(
                r'<p id="mt_watch-description" class="watch-description">\s+(.+?)\s+<\/p>',
                webpage, 'description', fatal=False
            )
        thumbnail = self._og_search_property(
            'image:secure_url', webpage, 'thumbnail'
        )
        uploader_id = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href=".+">(.+?)<\/a>',
            webpage, 'uploader', fatal=False
        )

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
            'formats': formats,
        }
