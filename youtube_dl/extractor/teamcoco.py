import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<url_title>.*)'
    _TEST = {
        u'url': u'http://teamcoco.com/video/louis-ck-interview-george-w-bush',
        u'file': u'19705.mp4',
        u'md5': u'cde9ba0fa3506f5f017ce11ead928f9a',
        u'info_dict': {
            u"description": u"Louis C.K. got starstruck by George W. Bush, so what? Part one.", 
            u"title": u"Louis C.K. Interview Pt. 1 11/3/11"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        url_title = mobj.group('url_title')
        webpage = self._download_webpage(url, url_title)

        video_id = self._html_search_regex(r'<article class="video" data-id="(\d+?)"',
            webpage, u'video id')

        self.report_extraction(video_id)

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data_xml = self._download_webpage(data_url, video_id, 'Downloading data webpage')
        data = xml.etree.ElementTree.fromstring(data_xml.encode('utf-8'))


        qualities = ['500k', '480p', '1000k', '720p', '1080p']
        formats = []
        for file in data.findall('files/file'):
            if file.attrib.get('playmode') == 'all':
                # it just duplicates one of the entries
                break
            file_url = file.text
            m_format = re.search(r'(\d+(k|p))\.mp4', file_url)
            if m_format is not None:
                format_id = m_format.group(1)
            else:
                format_id = file.attrib['bitrate']
            formats.append({
                'url': file_url,
                'ext': 'mp4',
                'format_id': format_id,
            })
        def sort_key(f):
            try:
                return qualities.index(f['format_id'])
            except ValueError:
                return -1
        formats.sort(key=sort_key)
        if not formats:
            raise RegexNotFoundError(u'Unable to extract video URL')

        return {
            'id':          video_id,
            'formats': formats,
            'title':       self._og_search_title(webpage),
            'thumbnail':   self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
