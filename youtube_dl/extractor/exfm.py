import re
import json

from .common import InfoExtractor


class ExfmIE(InfoExtractor):
    IE_NAME = u'exfm'
    IE_DESC = u'ex.fm'
    _VALID_URL = r'(?:http://)?(?:www\.)?ex\.fm/song/([^/]+)'
    _SOUNDCLOUD_URL = r'(?:http://)?(?:www\.)?api\.soundcloud.com/tracks/([^/]+)/stream'
    _TESTS = [
        {
            u'url': u'http://ex.fm/song/eh359',
            u'file': u'44216187.mp3',
            u'md5': u'e45513df5631e6d760970b14cc0c11e7',
            u'info_dict': {
                u"title": u"Test House \"Love Is Not Enough\" (Extended Mix) DeadJournalist Exclusive",
                u"uploader": u"deadjournalist",
                u'upload_date': u'20120424',
                u'description': u'Test House \"Love Is Not Enough\" (Extended Mix) DeadJournalist Exclusive',
            },
            u'note': u'Soundcloud song',
            u'skip': u'The site is down too often',
        },
        {
            u'url': u'http://ex.fm/song/wddt8',
            u'file': u'wddt8.mp3',
            u'md5': u'966bd70741ac5b8570d8e45bfaed3643',
            u'info_dict': {
                u'title': u'Safe and Sound',
                u'uploader': u'Capital Cities',
            },
            u'skip': u'The site is down too often',
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        song_id = mobj.group(1)
        info_url = "http://ex.fm/api/v3/song/%s" %(song_id)
        webpage = self._download_webpage(info_url, song_id)
        info = json.loads(webpage)
        song_url = info['song']['url']
        if re.match(self._SOUNDCLOUD_URL, song_url) is not None:
            self.to_screen('Soundcloud song detected')
            return self.url_result(song_url.replace('/stream',''), 'Soundcloud')
        return [{
            'id':          song_id,
            'url':         song_url,
            'ext':         'mp3',
            'title':       info['song']['title'],
            'thumbnail':   info['song']['image']['large'],
            'uploader':    info['song']['artist'],
            'view_count':  info['song']['loved_count'],
        }]
