from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    compat_urllib_parse,
    determine_ext,
    unified_strdate,
)


class NHLBaseInfoExtractor(InfoExtractor):
    @staticmethod
    def _fix_json(json_string):
        return json_string.replace('\\\'', '\'')

    def _extract_video(self, info):
        video_id = info['id']
        self.report_extraction(video_id)

        initial_video_url = info['publishPoint']
        data = compat_urllib_parse.urlencode({
            'type': 'fvod',
            'path': initial_video_url.replace('.mp4', '_sd.mp4'),
        })
        path_url = 'http://video.nhl.com/videocenter/servlets/encryptvideopath?' + data
        path_doc = self._download_xml(
            path_url, video_id, 'Downloading final video url')
        video_url = path_doc.find('path').text

        join = compat_urlparse.urljoin
        return {
            'id': video_id,
            'title': info['name'],
            'url': video_url,
            'ext': determine_ext(video_url),
            'description': info['description'],
            'duration': int(info['duration']),
            'thumbnail': join(join(video_url, '/u/'), info['bigImage']),
            'upload_date': unified_strdate(info['releaseDate'].split('.')[0]),
        }


class NHLIE(NHLBaseInfoExtractor):
    IE_NAME = 'nhl.com'
    _VALID_URL = r'https?://video(?P<team>\.[^.]*)?\.nhl\.com/videocenter/console(?:\?(?:.*?[?&])?)id=(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://video.canucks.nhl.com/videocenter/console?catid=6?id=453614',
        'info_dict': {
            'id': '453614',
            'ext': 'mp4',
            'title': 'Quick clip: Weise 4-3 goal vs Flames',
            'description': 'Dale Weise scores his first of the season to put the Canucks up 4-3.',
            'duration': 18,
            'upload_date': '20131006',
        },
    }, {
        'url': 'http://video.flames.nhl.com/videocenter/console?id=630616',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        json_url = 'http://video.nhl.com/videocenter/servlets/playlist?ids=%s&format=json' % video_id
        data = self._download_json(
            json_url, video_id, transform_source=self._fix_json)
        return self._extract_video(data[0])


class NHLVideocenterIE(NHLBaseInfoExtractor):
    IE_NAME = 'nhl.com:videocenter'
    IE_DESC = 'NHL videocenter category'
    _VALID_URL = r'https?://video\.(?P<team>[^.]*)\.nhl\.com/videocenter/(console\?.*?catid=(?P<catid>[0-9]+)(?![&?]id=).*?)?$'
    _TEST = {
        'url': 'http://video.canucks.nhl.com/videocenter/console?catid=999',
        'info_dict': {
            'id': '999',
            'title': 'Highlights',
        },
        'playlist_count': 12,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        team = mobj.group('team')
        webpage = self._download_webpage(url, team)
        cat_id = self._search_regex(
            [r'var defaultCatId = "(.+?)";',
             r'{statusIndex:0,index:0,.*?id:(.*?),'],
            webpage, 'category id')
        playlist_title = self._html_search_regex(
            r'tab0"[^>]*?>(.*?)</td>',
            webpage, 'playlist title', flags=re.DOTALL).lower().capitalize()

        data = compat_urllib_parse.urlencode({
            'cid': cat_id,
            # This is the default value
            'count': 12,
            'ptrs': 3,
            'format': 'json',
        })
        path = '/videocenter/servlets/browse?' + data
        request_url = compat_urlparse.urljoin(url, path)
        response = self._download_webpage(request_url, playlist_title)
        response = self._fix_json(response)
        if not response.strip():
            self._downloader.report_warning(u'Got an empty reponse, trying '
                                            'adding the "newvideos" parameter')
            response = self._download_webpage(request_url + '&newvideos=true',
                playlist_title)
            response = self._fix_json(response)
        videos = json.loads(response)

        return {
            '_type': 'playlist',
            'title': playlist_title,
            'id': cat_id,
            'entries': [self._extract_video(v) for v in videos],
        }
