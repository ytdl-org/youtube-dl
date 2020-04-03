from __future__ import unicode_literals

import re





from .common import InfoExtractor



class SonumaIE(InfoExtractor):

    _VALID_URL = r'(?:https?://)?(?:www\.)?sonuma\.be/archive/(?P<id>\w+[-0-9])*)'



    def _real_extract(self, url):

      	mobj=re.match(self._VALID_URL,url)



        video_id = mobj.group('id')

        webpage_url='https://sonuma.be/archive'+video_id

        webpage=self._download_webpage(webpage_url,video_id)



        self.report_extraction(video_id)



        video_url = self._html_search_regex('https://vod.infomaniak.com/redirect/sonumasa_2_vod/web2-39166/copy-32/cb88bd20-b57b-b756-e040-010a076419f5.mp4?sKey=1bc95ea22b94002d7a208593b7620d9f')



        return [{

            'id': video_id,

            'url': video_url,

            'ext': 'mp4',

            'title': self._og_search_title(webpage),

        }]