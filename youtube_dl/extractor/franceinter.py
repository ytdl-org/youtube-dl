import re

from .common import InfoExtractor
class FranceInterIE(InfoExtractor):
    
    _VALID_URL=r'http://www.franceinter.fr/player/reecouter\?play=(?P<id>[0-9]{6})'
    IE_NAME='FranceInter'
    
           
    #Easier to use python string matching than regex for a simple match
    def get_download_url(self,webpage):
        
        start=webpage.index('&urlAOD=')+8
        end=webpage.index('&startTime')
        return u'http://www.franceinter.fr/%s'%webpage[start:end]
        
    def get_title(self,webpage):
        start=webpage.index('<span class="title diffusion">')+30
        end=webpage.index('</span> dans')
        
        return webpage[start:end]
    def _real_extract(self,url):

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        webpage=self._download_webpage(url,video_id)
        
        title=self.get_title(webpage)
        
        video_url=self.get_download_url(webpage)
        
        return{'id': video_id,u'url': video_url,u'title': title}
         
        
