from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    find_xpath_attr,
    int_or_none,
    js_to_json,
    unescapeHTML,
)


class HowStuffWorksIE(InfoExtractor):
    _VALID_URL = r'https?://[\da-z-]+\.howstuffworks\.com/(?:[^/]+/)*(?:\d+-)?(?P<id>.+?)-video\.htm'
    _TESTS = [
        {
            'url': 'http://adventure.howstuffworks.com/5266-cool-jobs-iditarod-musher-video.htm',
            'info_dict': {
                'id': '450221',
                'ext': 'flv',
                'title': 'Cool Jobs - Iditarod Musher',
                'description': 'Cold sleds, freezing temps and warm dog breath... an Iditarod musher\'s dream. Kasey-Dee Gardner jumps on a sled to find out what the big deal is.',
                'display_id': 'cool-jobs-iditarod-musher',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 161,
            },
        },
        {
            'url': 'http://adventure.howstuffworks.com/7199-survival-zone-food-and-water-in-the-savanna-video.htm',
            'info_dict': {
                'id': '453464',
                'ext': 'mp4',
                'title': 'Survival Zone: Food and Water In the Savanna',
                'description': 'Learn how to find both food and water while trekking in the African savannah. In this video from the Discovery Channel.',
                'display_id': 'survival-zone-food-and-water-in-the-savanna',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://entertainment.howstuffworks.com/arts/2706-sword-swallowing-1-by-dan-meyer-video.htm',
            'info_dict': {
                'id': '440011',
                'ext': 'flv',
                'title': 'Sword Swallowing #1 by Dan Meyer',
                'description': 'Video footage (1 of 3) used by permission of the owner Dan Meyer through Sword Swallowers Association International <www.swordswallow.org>',
                'display_id': 'sword-swallowing-1-by-dan-meyer',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://shows.howstuffworks.com/stuff-to-blow-your-mind/optical-illusions-video.htm',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        clip_js = self._search_regex(
            r'(?s)var clip = ({.*?});', webpage, 'clip info')
        clip_info = self._parse_json(
            clip_js, display_id, transform_source=js_to_json)

        video_id = clip_info['content_id']
        formats = []
        m3u8_url = clip_info.get('m3u8')
        if m3u8_url:
            formats += self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        for video in clip_info.get('mp4', []):
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
                vbr = int_or_none(video.attrib['system-bitrate'], scale=1000)
                formats.append({
                    'url': '%s/%s%s' % (http_base, video.attrib['src'], URL_SUFFIX),
                    'format_id': '%dk' % vbr,
                    'vbr': vbr,
                })

        self._sort_formats(formats)

        return {
            'id': '%s' % video_id,
            'display_id': display_id,
            'title': unescapeHTML(clip_info['clip_title']),
            'description': unescapeHTML(clip_info.get('caption')),
            'thumbnail': clip_info.get('video_still_url'),
            'duration': clip_info.get('duration'),
            'formats': formats,
        }
