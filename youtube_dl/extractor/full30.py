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
            'title': 'Flamethrower Q&A with Charlie Hobson',
            'uploader' : 'Forgotten Weapons',
            'thumbnail': r're:^https?://.*52130\.jpg$',
            'ext': 'ogv',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1 [^>]*class=.video-title[^>]*>([^<]+?)</h1>', webpage, 'title', fatal=False, default=None) or self._og_search_title(webpage)
        uploader =  self._html_search_regex(r'<h1 class=.channel-title[^>]*>([^<]+)<', webpage, 'uploader', fatal=False, default=None) or None
        thumbnail = self._html_search_regex(r'<[^>]*property=.og:image. ?content="([^>]*thumbnails[^">]*)"\/>', webpage, 'thumbnail', fatal=False, default=None) or self._og_search_thumbnail(webpage)

        # looking for a line like the following
        # <input id="video-path" type="hidden" name="video_path" value="https://videos.full30.com/bitmotive/public/full30/v1.0/videos/forgottenweapons/b2a28b99494164ddd55e91a6c4648cbc/" />
        # there's also a full30.com/cdn which appears to have the same sort of structure. it's possible that either of these may go away so as a backup I'll build the cdn link out from channel slug
        vid_path = self._html_search_regex(r'<input id=.video-path[^>]*value=["\']([^"\']*)["\'][^>]*>', webpage, 'video_path', fatal=False, default=None)
        if not vid_path:
            channel_slug = self._html_search_regex(r'<input id=.channel-slug[^>]*value=["\']([^"\']*)["\'][^>]*>', webpage, 'channel_slug', fatal=True)
            vid_path = "https://www.full30.com/cdn/videos/" + channel_slug + "/" + video_id + "/"

        vid_json = self._download_webpage(vid_path, video_id)
        # turn sequence of json entries into an actual list
        vid_json = vid_json.rstrip()
        vid_json = "[" + vid_json + "]"
        vid_json = vid_json.replace("}", "},").replace(",]","]")
        parsed = self._parse_json(vid_json, video_id)

        formats = []
        for d in parsed:
            if d["type"] == "object":
                formats.append({
                    "url" : vid_path + d["name"],
                    "resolution" : d["name"][:d["name"].rfind(".")],
                    "filesize" : d["size"],
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'thumbnail' : thumbnail,
            'formats' : formats,
        }
