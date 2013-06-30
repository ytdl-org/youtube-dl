import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class BandcampIE(InfoExtractor):
    _VALID_URL = r'http://.*?\.bandcamp\.com/track/(?P<title>.*)'
    _TEST = {
        u'url': u'http://youtube-dl.bandcamp.com/track/youtube-dl-test-song',
        u'file': u'1812978515.mp3',
        u'md5': u'cdeb30cdae1921719a3cbcab696ef53c',
        u'info_dict': {
            u"title": u"youtube-dl test song \"'/\\\u00e4\u21ad"
        },
        u'skip': u'There is a limit of 200 free downloads / month for the test song'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        # We get the link to the free download page
        m_download = re.search(r'freeDownloadPage: "(.*?)"', webpage)
        if m_download is None:
            raise ExtractorError(u'No free songs found')

        download_link = m_download.group(1)
        id = re.search(r'var TralbumData = {(.*?)id: (?P<id>\d*?)$', 
                       webpage, re.MULTILINE|re.DOTALL).group('id')

        download_webpage = self._download_webpage(download_link, id,
                                                  'Downloading free downloads page')
        # We get the dictionary of the track from some javascrip code
        info = re.search(r'items: (.*?),$',
                         download_webpage, re.MULTILINE).group(1)
        info = json.loads(info)[0]
        # We pick mp3-320 for now, until format selection can be easily implemented.
        mp3_info = info[u'downloads'][u'mp3-320']
        # If we try to use this url it says the link has expired
        initial_url = mp3_info[u'url']
        re_url = r'(?P<server>http://(.*?)\.bandcamp\.com)/download/track\?enc=mp3-320&fsig=(?P<fsig>.*?)&id=(?P<id>.*?)&ts=(?P<ts>.*)$'
        m_url = re.match(re_url, initial_url)
        #We build the url we will use to get the final track url
        # This url is build in Bandcamp in the script download_bunde_*.js
        request_url = '%s/statdownload/track?enc=mp3-320&fsig=%s&id=%s&ts=%s&.rand=665028774616&.vrs=1' % (m_url.group('server'), m_url.group('fsig'), id, m_url.group('ts'))
        final_url_webpage = self._download_webpage(request_url, id, 'Requesting download url')
        # If we could correctly generate the .rand field the url would be
        #in the "download_url" key
        final_url = re.search(r'"retry_url":"(.*?)"', final_url_webpage).group(1)

        track_info = {'id':id,
                      'title' : info[u'title'],
                      'ext' :   'mp3',
                      'url' :   final_url,
                      'thumbnail' : info[u'thumb_url'],
                      'uploader' :  info[u'artist']
                      }

        return [track_info]
