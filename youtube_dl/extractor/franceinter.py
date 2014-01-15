from __future__ import unicode_literals

import re

from .common import InfoExtractor
class FranceInterIE(InfoExtractor):
    
    _VALID_URL=r'http://(?:www\.)?franceinter\.fr/player/reecouter\?play=(?P<id>[0-9]{6})'
    _TEST={
           u'url':u'http://www.franceinter.fr/player/reecouter?play=793962',
           u'file':u'793962.mp3'
                  
           }
           
   
        
   
    def _real_extract(self,url):

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        webpage=self._download_webpage(url,video_id)
        
        title=self._search_regex(u'(?<=<span class="roll_overflow">)(.*)(?=</span></h1>)', webpage, u'title')
        
        video_url='http://www.franceinter.fr/'+self._search_regex(u'(?<=&urlAOD=)(.*)(?=&startTime)', webpage, u'video url')
        
        return{'id': video_id,u'url': video_url,u'title': title}
        
        