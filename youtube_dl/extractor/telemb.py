import re
# -*- coding: utf-8 -*-
# needed for the title french ê!  coding utf-8- -*- 
# based on the vine.co and lots of help from https://filippo.io/add-support-for-a-new-video-site-to-youtube-dl/
from .common import InfoExtractor


class TelembIE(InfoExtractor):

    _VALID_URL = r'https?://www\.telemb\.be/(?P<id>.*)'

    _TEST = {
        u'url': u'http://www.telemb.be/mons-cook-with-danielle-des-cours-de-cuisine-en-anglais-_d_13466.html',
        u'file': u'mons-cook-with-danielle-des-cours-de-cuisine-en-anglais-_d_13466.html.mp4',
        u'md5': u'f45ea69878516ba039835794e0f8f783',
        u'info_dict': { 
            u"title": u'TéléMB : Mons - Cook with Danielle : des cours de cuisine en anglais ! - Les reportages'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.telemb.be/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)


        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'"(http://wowza\.imust\.org/srv/vod/.*\.mp4)"',
            webpage, u'video URL')

        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       'mp4',
            'title':     self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }]
