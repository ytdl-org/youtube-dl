from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import int_or_none


class PornHdIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?pornhd\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'md5': '956b8ca569f7f4d8ec563e2c41598441',
        'info_dict': {
            'id': '1962',
            'ext': 'mp4',
            'title': 'Sierra loves doing laundry',
            'description': 'md5:8ff0523848ac2b8f9b065ba781ccf294',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>(.+) porn HD.+?</title>', webpage, 'title')
        description = self._html_search_regex(
            r'<div class="description">([^<]+)</div>', webpage, 'description', fatal=False)
        view_count = int_or_none(self._html_search_regex(
            r'(\d+) views\s*</span>', webpage, 'view count', fatal=False))

        videos = re.findall(
            r'var __video([\da-zA-Z]+?)(Low|High)StreamUrl = \'(http://.+?)\?noProxy=1\'', webpage)

        mobj = re.search(r'flashVars = (?P<flashvars>{.+?});', webpage)
        if mobj:
            flashvars = json.loads(mobj.group('flashvars'))
            for key, quality in [('hashlink', 'low'), ('hd', 'high')]:
                redirect_url = flashvars.get(key)
                if redirect_url:
                    videos.append(('flv', quality, redirect_url))
            thumbnail = flashvars['urlWallpaper']
        else:
            thumbnail = self._og_search_thumbnail(webpage)

        formats = []
        for format_, quality, redirect_url in videos:
            format_id = '%s-%s' % (format_.lower(), quality.lower())
            video_url = self._download_webpage(
                redirect_url, video_id, 'Downloading %s video link' % format_id, fatal=False)
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'ext': format_.lower(),
                'format_id': format_id,
                'quality': 1 if quality.lower() == 'high' else 0,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
            'age_limit': 18,
        }
