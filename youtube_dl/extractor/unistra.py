import re

from .common import InfoExtractor

class UnistraIE(InfoExtractor):
    _VALID_URL = r'http://utv\.unistra\.fr/(?:index|video)\.php\?id_video\=(\d+)'

    _TEST = {
        u'url': u'http://utv.unistra.fr/video.php?id_video=154',
        u'file': u'154.mp4',
        u'md5': u'736f605cfdc96724d55bb543ab3ced24',
        u'info_dict': {
            u'title': u'M!ss Yella',
            u'description': u'md5:104892c71bd48e55d70b902736b81bbf',
        },
    }

    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, video_id)
        width = re.search(r'width: "(\d*?)",', webpage).group(1)
        height = re.search(r'height: "(\d*?)",', webpage).group(1)
        files = re.findall(r'file: "(.*?)"', webpage)
        video_url = 'http://vod-flash.u-strasbg.fr:8080'
        formats = [{
            'format_id': 'SD',
            'url': video_url + files[0],
            'ext': 'mp4',
            'resolution': width + 'x' + height
            }]
        if files[1] != files[0]:
            formats.append({
            'format_id': 'HD',
            'url': video_url + files[1],
            'ext': 'mp4'
            })
        title = self._html_search_regex(r'<title>UTV - (.*?)</', webpage, u'title')

        return {'id': video_id,
                'title': title,
                'description': self._html_search_regex(r'<meta name="Description" content="(.*?)"', webpage, u'description', flags=re.DOTALL),
                'thumbnail': self._search_regex(r'image: "(.*?)"', webpage, u'thumbnail'),
                'formats': formats
                }
