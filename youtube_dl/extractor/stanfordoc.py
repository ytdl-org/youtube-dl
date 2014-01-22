import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    orderedSet,
    unescapeHTML,
)


class StanfordOpenClassroomIE(InfoExtractor):
    IE_NAME = u'stanfordoc'
    IE_DESC = u'Stanford Open ClassRoom'
    _VALID_URL = r'^(?:https?://)?openclassroom\.stanford\.edu(?P<path>/?|(/MainFolder/(?:HomePage|CoursePage|VideoPage)\.php([?]course=(?P<course>[^&]+)(&video=(?P<video>[^&]+))?(&.*)?)?))$'
    _TEST = {
        u'url': u'http://openclassroom.stanford.edu/MainFolder/VideoPage.php?course=PracticalUnix&video=intro-environment&speed=100',
        u'file': u'PracticalUnix_intro-environment.mp4',
        u'md5': u'544a9468546059d4e80d76265b0443b8',
        u'info_dict': {
            u"title": u"Intro Environment"
        }
    }

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
            mdoc = self._download_xml(xmlUrl, info['id'])
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

            rootURL = 'http://openclassroom.stanford.edu/MainFolder/HomePage.php'
            rootpage = self._download_webpage(rootURL, info['id'],
                errnote=u'Unable to download course info page')

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
