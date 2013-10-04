import re
import xml.etree.ElementTree
import operator

from .common import InfoExtractor


class MetacriticIE(InfoExtractor):
    _VALID_URL = r'https?://www\.metacritic\.com/.+?/trailers/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.metacritic.com/game/playstation-4/infamous-second-son/trailers/3698222',
        u'file': u'3698222.mp4',
        u'info_dict': {
            u'title': u'inFamous: Second Son - inSide Sucker Punch: Smoke & Mirrors',
            u'description': u'Take a peak behind-the-scenes to see how Sucker Punch brings smoke into the universe of inFAMOUS Second Son on the PS4.',
            u'duration': 221,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        # The xml is not well formatted, there are raw '&'
        info_xml = self._download_webpage('http://www.metacritic.com/video_data?video=' + video_id,
            video_id, u'Downloading info xml').replace('&', '&amp;')
        info = xml.etree.ElementTree.fromstring(info_xml.encode('utf-8'))

        clip = next(c for c in info.findall('playList/clip') if c.find('id').text == video_id)
        formats = []
        for videoFile in clip.findall('httpURI/videoFile'):
            rate_str = videoFile.find('rate').text
            video_url = videoFile.find('filePath').text
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': rate_str,
                'rate': int(rate_str),
            })
        formats.sort(key=operator.itemgetter('rate'))

        description = self._html_search_regex(r'<b>Description:</b>(.*?)</p>',
            webpage, u'description', flags=re.DOTALL)

        info = {
            'id': video_id,
            'title': clip.find('title').text,
            'formats': formats,
            'description': description,
            'duration': int(clip.find('duration').text),
        }
        # TODO: Remove when #980 has been merged
        info.update(formats[-1])
        return info
