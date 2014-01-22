import re

from .common import InfoExtractor


class AnitubeIE(InfoExtractor):
    IE_NAME = u'anitube.se'
    _VALID_URL = r'https?://(?:www\.)?anitube\.se/video/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.anitube.se/video/36621',
        u'md5': u'59d0eeae28ea0bc8c05e7af429998d43',
        u'file': u'36621.mp4',
        u'info_dict': {
            u'id': u'36621',
            u'ext': u'mp4',
            u'title': u'Recorder to Randoseru 01',
        },
        u'skip': u'Blocked in the US',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        key = self._html_search_regex(r'http://www\.anitube\.se/embed/([A-Za-z0-9_-]*)',
                                      webpage, u'key')

        config_xml = self._download_xml('http://www.anitube.se/nuevo/econfig.php?key=%s' % key,
                                                key)

        video_title = config_xml.find('title').text

        formats = []
        video_url = config_xml.find('file')
        if video_url is not None:
            formats.append({
                'format_id': 'sd',
                'url': video_url.text,
            })
        video_url = config_xml.find('filehd')
        if video_url is not None:
            formats.append({
                'format_id': 'hd',
                'url': video_url.text,
            })

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats
        }
