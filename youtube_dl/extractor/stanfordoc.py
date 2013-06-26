import re
import socket
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_request,

    ExtractorError,
    orderedSet,
    unescapeHTML,
)


class StanfordOpenClassroomIE(InfoExtractor):
    """Information extractor for Stanford's Open ClassRoom"""

    _VALID_URL = r'^(?:https?://)?openclassroom.stanford.edu(?P<path>/?|(/MainFolder/(?:HomePage|CoursePage|VideoPage)\.php([?]course=(?P<course>[^&]+)(&video=(?P<video>[^&]+))?(&.*)?)?))$'
    IE_NAME = u'stanfordoc'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        if mobj.group('course') and mobj.group('video'): # A specific video
            course = mobj.group('course')
            video = mobj.group('video')
            info = {
                'id': course + '_' + video,
                'uploader': None,
                'upload_date': None,
            }

            self.report_extraction(info['id'])
            baseUrl = 'http://openclassroom.stanford.edu/MainFolder/courses/' + course + '/videos/'
            xmlUrl = baseUrl + video + '.xml'
            try:
                metaXml = compat_urllib_request.urlopen(xmlUrl).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))
            mdoc = xml.etree.ElementTree.fromstring(metaXml)
            try:
                info['title'] = mdoc.findall('./title')[0].text
                info['url'] = baseUrl + mdoc.findall('./videoFile')[0].text
            except IndexError:
                raise ExtractorError(u'Invalid metadata XML file')
            info['ext'] = info['url'].rpartition('.')[2]
            return [info]
        elif mobj.group('course'): # A course page
            course = mobj.group('course')
            info = {
                'id': course,
                'type': 'playlist',
                'uploader': None,
                'upload_date': None,
            }

            coursepage = self._download_webpage(url, info['id'],
                                        note='Downloading course info page',
                                        errnote='Unable to download course info page')

            info['title'] = self._html_search_regex('<h1>([^<]+)</h1>', coursepage, 'title', default=info['id'])

            info['description'] = self._html_search_regex('<description>([^<]+)</description>',
                coursepage, u'description', fatal=False)

            links = orderedSet(re.findall('<a href="(VideoPage.php\?[^"]+)">', coursepage))
            info['list'] = [
                {
                    'type': 'reference',
                    'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(vpage),
                }
                    for vpage in links]
            results = []
            for entry in info['list']:
                assert entry['type'] == 'reference'
                results += self.extract(entry['url'])
            return results
        else: # Root page
            info = {
                'id': 'Stanford OpenClassroom',
                'type': 'playlist',
                'uploader': None,
                'upload_date': None,
            }

            self.report_download_webpage(info['id'])
            rootURL = 'http://openclassroom.stanford.edu/MainFolder/HomePage.php'
            try:
                rootpage = compat_urllib_request.urlopen(rootURL).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download course info page: ' + compat_str(err))

            info['title'] = info['id']

            links = orderedSet(re.findall('<a href="(CoursePage.php\?[^"]+)">', rootpage))
            info['list'] = [
                {
                    'type': 'reference',
                    'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(cpage),
                }
                    for cpage in links]

            results = []
            for entry in info['list']:
                assert entry['type'] == 'reference'
                results += self.extract(entry['url'])
            return results
