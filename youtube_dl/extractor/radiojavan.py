# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import(
    parse_duration,
    str_to_int
)

class RadioJavanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/videos/video/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - Ashoobam',
            'description': 'Chaartaar - Ashoobam',
            'thumbnail': 're:^https?://.*\.jpe?g$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        urls = list()
        prefix = 'https://media.rdjavan.com/media/music_video/'

        video_url_480 = self._search_regex(
            r'RJ\.video480p = \'([^\']+)\'', webpage, '480 video url', fatal= False)
        video_url_720 = self._search_regex(
            r'RJ\.video720p = \'([^\']+)\'', webpage, '720 video url', fatal= False)
        video_url_1080 = self._search_regex(
            r'RJ\.video1080p = \'([^\']+)\'', webpage, '1080 video url', fatal= False)

        if video_url_480:
            urls.append({'url': prefix + video_url_480, 'format': '480p'})
        if video_url_720:
            urls.append({'url': prefix + video_url_720, 'format': '720p'})
        if video_url_1080:
            urls.append({'url': prefix + video_url_1080, 'format': '1080p'})

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        formats = [{
            'url': url['url'],
            'format': url['format']
        } for url in urls]

        likes = self._search_regex(
            r'<span class="rating">([\d,]+)\s*likes</span>', webpage, 'Likes Count', fatal=False )
        likes = likes.replace(',', '')
        dislikes = self._search_regex(
            r'<span class="rating">([\d,]+)\s*dislikes</span>', webpage, 'Dislikes Count', fatal=False )
        dislikes = dislikes.replace(',', '')

        plays = self._search_regex(
            r'views_publish[">\s]*<span[^>]+class="views">Plays: ([\d,]+)</span>', webpage, 'Play Count', fatal=False )
        plays = plays.replace(',', '')

        return {
            'formats': formats,
            'id': display_id,
            'title': title,
            'description': title, # no description provided in RadioJavan
            'thumbnail': thumbnail,
            'like_count': str_to_int(likes),
            'dislike_count': str_to_int(dislikes),
            'viewCount': str_to_int(plays)
        }