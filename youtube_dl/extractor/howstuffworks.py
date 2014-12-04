from __future__ import unicode_literals

from .common import InfoExtractor


class HowStuffWorksIE(InfoExtractor):
    _VALID_URL = r'https?://[\da-z-]+\.howstuffworks\.com/(?:[^/]+/)*\d+-(?P<id>.+?)-video\.htm'
    _TESTS = [
        {
            'url': 'http://adventure.howstuffworks.com/39521-deadliest-catch-nautical-collision-video.htm',
            'info_dict': {
                'id': '553475',
                'ext': 'mp4',
                'title': 'Deadliest Catch: Nautical Collision',
                'description': 'Check out this clip to get an exclusive look at the Deadliest Catch crew back in action.',
                'thumbnail': 'http://s.hswstatic.com/gif/videos/480x360/39521.jpg',
            },
        },
        {
            'url': 'http://adventure.howstuffworks.com/7199-survival-zone-food-and-water-in-the-savanna-video.htm',
            'info_dict': {
                'id': '453464',
                'ext': 'mp4',
                'title': 'Survival Zone: Food and Water In the Savanna',
                'description': 'Learn how to find both food and water while trekking in the African savannah. In this video from the Discovery Channel.',
                'thumbnail': 'http://s.hswstatic.com/gif/videos/480x360/7199.jpg',
            },
        },
        {
            'url': 'http://entertainment.howstuffworks.com/arts/34476-time-warp-fire-breathing-disaster-video.htm',
            'info_dict': {
                'id': '487036',
                'ext': 'mp4',
                'title': 'Time Warp: Fire-Breathing Disaster',
                'description': 'Fire-breathers are safe from flames when they angle their heads up as they blow -- see what would happen if they looked down instead. Check out this clip from Discovery\'s "Time Warp" series to learn more.',
                'thumbnail': 'http://s.hswstatic.com/gif/videos/480x360/34476.jpg',
            },
        },
    ]

    def _extract_clip_info(self, key, clip_info, name=None, **kargs):
        if name is None:
            name = key
        return self._html_search_regex(
            r"\s*%s\s*: '?([^'\n]*[^'\n,])" % key, clip_info, name, **kargs)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        clip_info = self._search_regex('(?s)var clip = {(.*?)};', webpage, 'clip info')
        video_id = self._extract_clip_info('content_id', clip_info, 'video id')
        formats = []
        m3u8_url = self._extract_clip_info('m3u8', clip_info, 'm3u8 url', default=None)
        if m3u8_url is not None:
            formats += self._extract_m3u8_formats(m3u8_url , video_id, 'mp4')
        mp4 = self._parse_json(
            self._extract_clip_info(
                'mp4', clip_info, 'formats').replace('},]','}]'), video_id)
        for video in mp4:
            formats.append({
                'url': video['src'],
                'format_id': video['bitrate'],
                'tbr': int(video['bitrate'].rstrip('k')),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': self._extract_clip_info('clip_title', clip_info, 'title'),
            'description': self._extract_clip_info('caption', clip_info, 'description', fatal=False),
            'thumbnail': self._extract_clip_info('video_still_url', clip_info, 'thumbnail'),
            'duration': self._extract_clip_info('duration', clip_info),
            'formats': formats,
        }
