import re,random

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)

class FKTVIE(InfoExtractor):
    """Information Extractor for Fernsehkritik-TV"""
    _VALID_URL = r'(?:http://)?(?:www\.)?fernsehkritik.tv/folge-(?P<ep>[0-9]+)(?:/.*)?'

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        episode = int(mobj.group('ep'))
        
        server = random.randint(2,4)
        video_thumbnail = 'http://fernsehkritik.tv/images/magazin/folge%d.jpg' % episode
        videos = []
        # Download all three parts
        for i in range(1,4):
            video_id = '%04d%d' % (episode, i)
            video_url = 'http://dl%d.fernsehkritik.tv/fernsehkritik%d%s.flv' % (server, episode, '' if i==1 else '-%d'%i)
            video_title = 'Fernsehkritik %d.%d' % (episode, i)
            videos.append({
                'id':       video_id,
                'url':      video_url,
                'ext':      determine_ext(video_url),
                'title':    video_title,
                'thumbnail': video_thumbnail
            })
        return videos

class FKTVPosteckeIE(InfoExtractor):
    """Information Extractor for Fernsehkritik-TV Postecke"""
    _VALID_URL = r'(?:http://)?(?:www\.)?fernsehkritik.tv/inline-video/postecke.php\?(.*&)?ep=(?P<ep>[0-9]+)(&|$)'
    _TEST = {
        u'url': u'http://fernsehkritik.tv/inline-video/postecke.php?iframe=true&width=625&height=440&ep=120',
        u'file': u'0120.flv',
        u'md5': u'262f0adbac80317412f7e57b4808e5c4',
        u'info_dict': {
            u"title": u"Postecke 120"
        }
    }

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        episode = int(mobj.group('ep'))
        
        server = random.randint(2,4)
        video_id = '%04d' % episode
        video_url = 'http://dl%d.fernsehkritik.tv/postecke/postecke%d.flv' % (server, episode)
        video_title = 'Postecke %d' % episode
        return[{
            'id':       video_id,
            'url':      video_url,
            'ext':      determine_ext(video_url),
            'title':    video_title,
        }]
