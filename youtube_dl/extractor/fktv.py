import re
import random
import json

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    get_element_by_id,
    clean_html,
)


class FKTVIE(InfoExtractor):
    IE_NAME = u'fernsehkritik.tv'
    _VALID_URL = r'(?:http://)?(?:www\.)?fernsehkritik\.tv/folge-(?P<ep>[0-9]+)(?:/.*)?'

    _TEST = {
        u'url': u'http://fernsehkritik.tv/folge-1',
        u'file': u'00011.flv',
        u'info_dict': {
            u'title': u'Folge 1 vom 10. April 2007',
            u'description': u'md5:fb4818139c7cfe6907d4b83412a6864f',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        episode = int(mobj.group('ep'))

        server = random.randint(2, 4)
        video_thumbnail = 'http://fernsehkritik.tv/images/magazin/folge%d.jpg' % episode
        start_webpage = self._download_webpage('http://fernsehkritik.tv/folge-%d/Start' % episode,
            episode)
        playlist = self._search_regex(r'playlist = (\[.*?\]);', start_webpage,
            u'playlist', flags=re.DOTALL)
        files = json.loads(re.sub('{[^{}]*?}', '{}', playlist))
        # TODO: return a single multipart video
        videos = []
        for i, _ in enumerate(files, 1):
            video_id = '%04d%d' % (episode, i)
            video_url = 'http://dl%d.fernsehkritik.tv/fernsehkritik%d%s.flv' % (server, episode, '' if i == 1 else '-%d' % i)
            videos.append({
                'id': video_id,
                'url': video_url,
                'ext': determine_ext(video_url),
                'title': clean_html(get_element_by_id('eptitle', start_webpage)),
                'description': clean_html(get_element_by_id('contentlist', start_webpage)),
                'thumbnail': video_thumbnail
            })
        return videos


class FKTVPosteckeIE(InfoExtractor):
    IE_NAME = u'fernsehkritik.tv:postecke'
    _VALID_URL = r'(?:http://)?(?:www\.)?fernsehkritik\.tv/inline-video/postecke\.php\?(.*&)?ep=(?P<ep>[0-9]+)(&|$)'
    _TEST = {
        u'url': u'http://fernsehkritik.tv/inline-video/postecke.php?iframe=true&width=625&height=440&ep=120',
        u'file': u'0120.flv',
        u'md5': u'262f0adbac80317412f7e57b4808e5c4',
        u'info_dict': {
            u"title": u"Postecke 120"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        episode = int(mobj.group('ep'))

        server = random.randint(2, 4)
        video_id = '%04d' % episode
        video_url = 'http://dl%d.fernsehkritik.tv/postecke/postecke%d.flv' % (server, episode)
        video_title = 'Postecke %d' % episode
        return {
            'id':       video_id,
            'url':      video_url,
            'ext':      determine_ext(video_url),
            'title':    video_title,
        }
