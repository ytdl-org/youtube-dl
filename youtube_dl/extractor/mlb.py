from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MlbIE(InfoExtractor):
    _VALID_URL = r'http?://m\.mlb\.com/video/topic/[0-9]+/v(?P<id>n?\d+)/.*$'
    _TEST = {
        'url': 'http://m.mlb.com/video/topic/81536970/v34496663/mianym-stanton-practices-for-the-home-run-derby',
        'md5': u'd9c022c10d21f849f49c05ae12a8a7e9',
        'info_dict': {
            'id': '34496663',
            'ext': 'mp4',
            'format': 'mp4',
            'description': "7/11/14: Giancarlo Stanton practices for the Home Run Derby prior to the game against the Mets",
            'title': "Stanton prepares for Derby",
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=video_id)
        description = self._html_search_regex(r'<meta name="description" (?:content|value)="(.*?)"/>', webpage, 'description', fatal=False)
        thumbnail = self._html_search_regex(r'<meta itemprop="image" (?:content|value)="(.*?)" />', webpage, 'image', fatal=False)

        # use the video_id to find the Media detail XML
        id_len = len(video_id)
        _mediadetail_url = 'http://m.mlb.com/gen/multimedia/detail/'+video_id[id_len-3]+'/'+video_id[id_len-2]+'/'+video_id[id_len-1]+'/'+video_id+'.xml'
        
        mediadetails = self._download_xml(_mediadetail_url, video_id, "Downloading media detail...")
        has1500K = 0
        has1200K = 0
        has600K = 0
        # loop through the list of url's and only get the highest quality MP4 content
        for element in mediadetails.findall('url'):
            scenario = element.attrib['playback_scenario']
            if scenario.startswith(u'FLASH'):
                if scenario.startswith(u'FLASH_1800K'):
                    video_url = element.text
                    # 1800K is the current highest quality video on MLB.com
                    break
                else:
                    if scenario.startswith(u'FLASH_1500K'):
                        video_url = element.text
                        has1500K = 1
                    else:
                        if (scenario.startswith(u'FLASH_1200K') and not has1500K):
                            video_url = element.text
                            has1200K = 1
                        else:
                            if (scenario.startswith(u'FLASH_600K') and not has1200K):
                                video_url = element.text
                                has600K = 1
                            else:
                                if (scenario.startswith(u'FLASH_300K') and not has600K):
                                    video_url = element.text

        return {
            'id': video_id,
            'url': video_url,
            'extractor': 'mlb',
            'webpage_url': url,
            'title': title,
            'ext': 'mp4',
            'format': 'mp4',
            'description': description,
            'thumbnail': thumbnail,
        }
