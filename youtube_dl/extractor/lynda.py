from __future__ import unicode_literals

import re
import json

from .subtitles import SubtitlesInfoExtractor
from .common import InfoExtractor
from ..utils import ExtractorError


class LyndaIE(SubtitlesInfoExtractor):
    IE_NAME = 'lynda'
    IE_DESC = 'lynda.com videos'
    _VALID_URL = r'https?://www\.lynda\.com/[^/]+/[^/]+/\d+/(\d+)-\d\.html'

    _TEST = {
        'url': 'http://www.lynda.com/Bootstrap-tutorials/Using-exercise-files/110885/114408-4.html',
        'file': '114408.mp4',
        'md5': 'ecfc6862da89489161fb9cd5f5a6fac1',
        u"info_dict": {
            'title': 'Using the exercise files',
            'duration': 68
        }
    }
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        page = self._download_webpage('http://www.lynda.com/ajax/player?videoId=%s&type=video' % video_id,
                                      video_id, 'Downloading video JSON')
        video_json = json.loads(page)

        if 'Status' in video_json and video_json['Status'] == 'NotFound':
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        if video_json['HasAccess'] is False:
            raise ExtractorError('Video %s is only available for members' % video_id, expected=True)

        video_id = video_json['ID']
        duration = video_json['DurationInSeconds']
        title = video_json['Title']

        formats = [{'url': fmt['Url'],
                    'ext': fmt['Extension'],
                    'width': fmt['Width'],
                    'height': fmt['Height'],
                    'filesize': fmt['FileSize'],
                    'format_id': str(fmt['Resolution'])
                    } for fmt in video_json['Formats']]

        self._sort_formats(formats)
        
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, page)
            return
        
        subtitles = self._fix_subtitles(self.extract_subtitles(video_id, page))
        
        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'subtitles': subtitles,
            'formats': formats
        }
        
    _TIMECODE_REGEX = r'\[(?P<timecode>\d+:\d+:\d+[\.,]\d+)\]'    
    
    def _fix_subtitles(self, subtitles):
        fixed_subtitles = {}
        for k, v in subtitles.items():
            subs = json.loads(v)
            if len(subs) == 0:
                continue
            srt = ''
            for pos in range(0, len(subs) - 1):
                seq_current = subs[pos]                
                m_current = re.match(self._TIMECODE_REGEX, seq_current['Timecode'])
                if m_current is None:
                    continue                
                seq_next = subs[pos+1]
                m_next = re.match(self._TIMECODE_REGEX, seq_next['Timecode'])
                if m_next is None:
                    continue                
                appear_time = m_current.group('timecode')
                disappear_time = m_next.group('timecode')
                text = seq_current['Caption']
                srt += '%s\r\n%s --> %s\r\n%s' % (str(pos), appear_time, disappear_time, text)
            if srt:
                fixed_subtitles[k] = srt
        return fixed_subtitles
        
    def _get_available_subtitles(self, video_id, webpage):
        url = 'http://www.lynda.com/ajax/player?videoId=%s&type=transcript' % video_id
        sub = self._download_webpage(url, None, note=False)
        sub_json = json.loads(sub)
        return {'en': url} if len(sub_json) > 0 else {}


class LyndaCourseIE(InfoExtractor):
    IE_NAME = 'lynda:course'
    IE_DESC = 'lynda.com online courses'

    # Course link equals to welcome/introduction video link of same course
    # We will recognize it as course link
    _VALID_URL = r'https?://(?:www|m)\.lynda\.com/(?P<coursepath>[^/]+/[^/]+/(?P<courseid>\d+))-\d\.html'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('coursepath')
        course_id = mobj.group('courseid')

        page = self._download_webpage('http://www.lynda.com/ajax/player?courseId=%s&type=course' % course_id,
                                      course_id, 'Downloading course JSON')
        course_json = json.loads(page)

        if 'Status' in course_json and course_json['Status'] == 'NotFound':
            raise ExtractorError('Course %s does not exist' % course_id, expected=True)

        unaccessible_videos = 0
        videos = []

        for chapter in course_json['Chapters']:
            for video in chapter['Videos']:
                if video['HasAccess'] is not True:
                    unaccessible_videos += 1
                    continue
                videos.append(video['ID'])

        if unaccessible_videos > 0:
            self._downloader.report_warning('%s videos are only available for members and will not be downloaded' % unaccessible_videos)

        entries = [
            self.url_result('http://www.lynda.com/%s/%s-4.html' %
                            (course_path, video_id),
                            'Lynda')
            for video_id in videos]

        course_title = course_json['Title']

        return self.playlist_result(entries, course_id, course_title)
