from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import find_xpath_attr


class HowStuffWorksIE(InfoExtractor):
    _VALID_URL = r'https?://[\da-z-]+\.howstuffworks\.com/(?:[^/]+/)*\d+-(?P<id>.+?)-video\.htm'
    _TESTS = [
        {
            'url': 'http://adventure.howstuffworks.com/5266-cool-jobs-iditarod-musher-video.htm',
            'info_dict': {
                'id': '450221',
                'ext': 'flv',
                'title': 'Cool Jobs - Iditarod Musher',
                'description': 'Cold sleds, freezing temps and warm dog breath... an Iditarod musher\'s dream. Kasey-Dee Gardner jumps on a sled to find out what the big deal is.',
                'thumbnail': 'http://s.hswstatic.com/gif/videos/480x360/5266.jpg',
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
            'url': 'http://entertainment.howstuffworks.com/arts/2706-sword-swallowing-1-by-dan-meyer-video.htm',
            'info_dict': {
                'id': '440011',
                'ext': 'flv',
                'title': 'Sword Swallowing #1 by Dan Meyer',
                'description': 'Video footage (1 of 3) used by permission of the owner Dan Meyer through Sword Swallowers Association International <www.swordswallow.org>',
                'thumbnail': 'http://s.hswstatic.com/gif/videos/480x360/118306353233.jpg',
            },
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        clip_info = self._search_regex('(?s)var clip = {(.*?)};', webpage, 'clip info')

        def extract_clip_info(key, clip_info, name=None, **kargs):
            if name is None:
                name = key
            return self._html_search_regex(
                r"\s*%s\s*: '?([^'\n]*[^'\n,])" % key, clip_info, name, **kargs)

        video_id = extract_clip_info('content_id', clip_info, 'video id')
        formats = []
        m3u8_url = extract_clip_info('m3u8', clip_info, 'm3u8 url', default=None)
        if m3u8_url is not None:
            formats += self._extract_m3u8_formats(m3u8_url , video_id, 'mp4')
        mp4 = self._parse_json(
            extract_clip_info(
                'mp4', clip_info, 'formats').replace('},]','}]'), video_id)
        for video in mp4:
            formats.append({
                'url': video['src'],
                'format_id': video['bitrate'],
                'vbr': int(video['bitrate'].rstrip('k')),
            })

        if not formats:
            smil = self._download_xml(
                'http://services.media.howstuffworks.com/videos/%s/smil-service.smil' % video_id,
                video_id, 'Downloading video SMIL')

            http_base = find_xpath_attr(
                smil,
                './{0}head/{0}meta'.format('{http://www.w3.org/2001/SMIL20/Language}'),
                'name',
                'httpBase').get('content')

            URL_SUFFIX = '?v=2.11.3&fp=LNX 11,2,202,356&r=A&g=A'

            for video in smil.findall(
                    './{0}body/{0}switch/{0}video'.format('{http://www.w3.org/2001/SMIL20/Language}')):
                vbr = int(video.attrib['system-bitrate']) / 1000
                formats.append({
                    'url': '%s/%s%s' % (http_base, video.attrib['src'], URL_SUFFIX),
                    'format_id': '%dk' % vbr,
                    'vbr': vbr,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': extract_clip_info('clip_title', clip_info, 'title'),
            'description': extract_clip_info('caption', clip_info, 'description', fatal=False),
            'thumbnail': extract_clip_info('video_still_url', clip_info, 'thumbnail'),
            'duration': extract_clip_info('duration', clip_info),
            'formats': formats,
        }
