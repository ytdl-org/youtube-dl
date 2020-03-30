# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    try_get,
    mimetype2ext,
    clean_html
)


class AxiosIE(InfoExtractor):
    IE_NAME = 'axios'
    IE_DESC = 'www.axios.com'
    _VALID_URL = r"""(?x)^
            ((http[s]?|fpt):)\/?\/(www\.|m\.|)
                (?P<site>
                    (www\.axios\.com)
                )\/
            (?P<slug>.*?)\-
            (?P<id>[0-9a-z]{8}\-[0-9a-z]{4}-[a-z0-9]{4}.+?)\.
        """
    __TESTS = [
        {
            "url": r"https://www.axios.com/trump-coronavirus-restrictions-c3da2d28-b761-4b62-b6d6-734c059c6dba.html",
            "info_dict": {
                "id": "c3da2d28-b761-4b62-b6d6-734c059c6dba",
                "title": '''Trump says he wants to "open" the country by Easter''',
                "ext": "mp4",
                "description": str,
                'thumbnails': [],
            }
        },
        {
            "url": r"https://www.axios.com/coronavirus-texas-official-grandparents-die-172ca951-891c-44e7-a9ec-77c486e0c5c3.html",
            "info_dict": {
                "id": "172ca951-891c-44e7-a9ec-77c486e0c5c3",
                "title": '''Texas Lt. Gov.: Grandparents would be willing to die to save the economy''',
                "ext": "mp4",
                "description": str,
                'thumbnails': [],
            }
        },
        {
            "url": r"https://www.axios.com/cuomo-trump-mandatory-quarantine-panic-35ae54a1-0aa9-4a38-910d-647293002fc2.html",
            "info_dict": {
                "id": "35ae54a1-0aa9-4a38-910d-647293002fc2",
                "title": '''Cuomo: Trump's mandatory quarantine comments "really panicked people"''',
                "ext": "mp4",
                "description": str,
                'thumbnails': [],
            }
        },
        {
            "url": r"https://www.axios.com/coronavirus-louisiana-bel-edwards-ventilators-7810fc76-1825-41b2-8b22-f1cfc14e2ffe.html",
            "info_dict": {
                "id": "7810fc76-1825-41b2-8b22-f1cfc14e2ffe",
                "title": '''Louisiana on track to exceed ventilator capacity this week, governor says''',
                "ext": "mp4",
                "description": str,
                'thumbnails': [],
            }
        },
    ]
    api_jwplayer = r'http://content.jwplatform.com/v2/media/%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url_or_request=url,
            video_id=video_id
        )
        jwplayer_mobj = re.search(
            r'''<amp-jwplayer.+?data-player-id=\"(?P<player_id>.+?)\".+?data-media-id=\"(?P<media_id>.+?)\".+?\>\<\/amp-jwplayer>''',
            webpage
        )
        description = self._search_regex(
            r'''<div\s+class=\"b0w77w-0 jctzOA gtm-story-text\"\>(?P<description>.*?)\<\/div\>''',
            webpage, "Description", group="description"
        )
        title = self._search_regex(
            r'''<h1\s+class="sc-31t5q3-0 sc-1fjk95c-2 guveJc"\>(?P<title>.*?)\<\/h1\>''',
            webpage, "Title", group="title"
        )
        description = clean_html(description)
        # player_id = jwplayer_mobj.group("player_id")
        media_id = jwplayer_mobj.group("media_id")
        json_jwplayer = self._download_json(
            url_or_request=self.api_jwplayer % media_id,
            video_id=media_id,
        )
        playlist = try_get(json_jwplayer, lambda x: x['playlist'][0])
        if playlist:
            images = playlist.get('images')
            thumbnails = [
                {
                    "url": img.get('src'),
                    "width": img.get('width')
                } for img in images if img.get('src')
            ]
            sources = playlist.get('sources') or []
            formats = []
            for sour in sources:
                if not sour:
                    continue
                _type = sour.get('type')
                ext = mimetype2ext(_type)
                file = sour.get('file')
                if ext == 'm3u8':
                    m3u8_doc = self._download_webpage(file, video_id=media_id)
                    formats.extend(self._parse_m3u8_formats(m3u8_doc, file))
                elif ext == 'mp4':
                    formats.append({
                        "url": file,
                        "ext": ext,
                        "height": sour.get('height'),
                        "width": sour.get('width'),
                        'protocol': 'http',
                        "label": sour.get("label")
                    })
                else:
                    formats.append({
                        "url": file,
                        "ext": ext,
                        'protocol': 'http',
                        "label": sour.get("label")
                    })
            formats.sort(key=lambda x: x.get("height") if x.get("height") else -1)
            return {
                "id": video_id,
                "title": title.strip(),
                "thumbnails": thumbnails,
                "formats": formats,
                "description": description
            }
