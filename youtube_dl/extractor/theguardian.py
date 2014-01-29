import re
from .common import InfoExtractor
class TheGuardianIE(InfoExtractor):
     _VALID_URL = r'http://(?:www\.)?theguardian\.com/.*/.*/.*/.*/(?P<video_id>.*)/?'

     _TEST = {
    u'url': u'http://www.theguardian.com/world/video/2014/jan/29/president-barack-obama-state-union-address-video',
    u'file': u'president-barack-obama-state-union-address-video.mp4',
    u'md5': u'c3c4d57157bd28a20e877a0ec796a6cc',
    u'info_dict': {
        u"title": u"President Barack Obama delivers State of the Union address – video"
    }
}

     def _real_extract(self, url):
       mobj = re.match(self._VALID_URL, url)
       video_id = (mobj.group('video_id'))
       webpage_url = (url)
       webpage = self._download_webpage(webpage_url, video_id)  
       # Log that we are starting to parse the page.
       self.report_extraction(video_id)
       # Search for the video url (which is always a .mp4 file; the path to which is set in the JSON JWPlayerOptions() object.)
       # Sometimes there's whitespace that also needs to be accounted for. 
       video_url  = self._html_search_regex(r'file\s*:\s*\'(.*)\',', webpage, u'video URL') # e.g. file : 'video.mp4'

       return [{
          'id':        video_id,
          'url':       video_url,
          'ext':       'mp4',
          'title':     self._og_search_title(webpage),
      }]
