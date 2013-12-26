import re
import json

from .common import InfoExtractor
from ..utils import ExtractorError


class LyndaIE(InfoExtractor):
    IE_NAME = u'lynda'
    IE_DESC = u'lynda.com videos'
    _VALID_URL = r'https?://www\.lynda\.com/[^/]+/[^/]+/\d+/(\d+)-\d\.html'

    _TEST = {
        u'url': u'http://www.lynda.com/Bootstrap-tutorials/Using-exercise-files/110885/114408-4.html',
        u'file': u'114408.mp4',
        u'md5': u'ecfc6862da89489161fb9cd5f5a6fac1',
        u"info_dict": {
            u'title': u'Using the exercise files',
            u'duration': 68
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        page = self._download_webpage('http://www.lynda.com/ajax/player?videoId=%s&type=video' % video_id,
                                      video_id, u'Downloading video JSON')
        video_json = json.loads(page)

        if u'Status' in video_json and video_json[u'Status'] == u'NotFound':
            raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)

        if video_json[u'HasAccess'] is False:
            raise ExtractorError(u'Video %s is only available for members' % video_id, expected=True)

        video_id = video_json[u'ID']
        duration = video_json[u'DurationInSeconds']
        title = video_json[u'Title']

        formats = [{'url': fmt[u'Url'],
                    'ext': fmt[u'Extension'],
                    'width': fmt[u'Width'],
                    'height': fmt[u'Height'],
                    'filesize': fmt[u'FileSize'],
                    'format_id': fmt[u'Resolution']
                    } for fmt in video_json[u'Formats']]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'formats': formats
        }


class LyndaCourseIE(InfoExtractor):
    IE_NAME = u'lynda:course'
    IE_DESC = u'lynda.com online courses'

    # Course link equals to welcome/introduction video link of same course
    # We will recognize it as course link
    _VALID_URL = r'https?://(?:www|m)\.lynda\.com/(?P<coursepath>[^/]+/[^/]+/(?P<courseid>\d+))-\d\.html'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('coursepath')
        course_id = mobj.group('courseid')

        page = self._download_webpage('http://www.lynda.com/ajax/player?courseId=%s&type=course' % course_id,
                                      course_id, u'Downloading course JSON')
        course_json = json.loads(page)

        if u'Status' in course_json and course_json[u'Status'] == u'NotFound':
            raise ExtractorError(u'Course %s does not exist' % course_id, expected=True)

        unaccessible_videos = 0
        videos = []

        for chapter in course_json[u'Chapters']:
            for video in chapter[u'Videos']:
                if video[u'HasAccess'] is not True:
                    unaccessible_videos += 1
                    continue
                videos.append(video[u'ID'])

        if unaccessible_videos > 0:
            self._downloader.report_warning(u'%s videos are only available for members and will not be downloaded' % unaccessible_videos)

        entries = [self.url_result('http://www.lynda.com/%s/%s-4.html' % (course_path, video_id), 'Lynda') for video_id in videos]

        course_title = course_json[u'Title']

        return self.playlist_result(entries, course_id, course_title)