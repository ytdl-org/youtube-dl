# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class Full30IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?full30\.com/video/(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'http://www.full30.com/video/b2a28b99494164ddd55e91a6c4648cbc',
        'md5': 'f5aa3862cbe35c2083ce050ac1a5eb06',
        'info_dict': {
            'id': 'b2a28b99494164ddd55e91a6c4648cbc',
            'ext': 'ogv',
            'title': 'Flamethrower Q&A with Charlie Hobson',
            'thumbnail': r're:^https?://.*52130\.jpg$',
            'uploader' : 'Forgotten Weapons',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1 [^>]*class=.video-title[^>]*>([^<]+?)</h1>', webpage, 'title')
        uploader =  self._html_search_regex(r'<h1 class=.channel-title[^>]*>([^<]+)<', webpage, 'uploader', fatal=False)
        description = self._og_search_description(webpage)
        thumbnail = self._html_search_regex(r'<[^>]*property=.og:image. ?content="([^>]*thumbnails[^">]*)"\/>', webpage, 'thumbnail', fatal=False) or self._og_search_thumbnail(webpage)

        vidpath = self._html_search_regex(r'<input id=.video-path[^>]*value=["\']([^"\']*)["\'][^>]*>', webpage, 'video_path', fatal=False)
        vidjson = self._download_webpage(vidpath, video_id)
        # this is robust
        vidjson = vidjson.rstrip()
        vidjson = "[" + vidjson + "]"
        vidjson = vidjson.replace("}", "},").replace(",]","]")
        parsed = self._parse_json(vidjson, video_id)

        formats = []
        for d in parsed:
            if d["type"] == "object":
                formats.append({
                    "url" : vidpath + d["name"],
                    "resolution" : d["name"][:d["name"].rfind(".")],
                    "filesize" : d["size"],
                    "protocol" : "https"
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            # 'description': description,
            'uploader': uploader,
            # 'url' : url,
            'formats' : formats,
            # TODO more properties (see youtube_dl/extractor/common.py)
            'ext': 'mp4',
            'thumbnail' : thumbnail,
        }
