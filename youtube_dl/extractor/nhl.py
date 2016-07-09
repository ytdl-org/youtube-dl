from __future__ import unicode_literals

import re
import json
import os

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
    compat_str,
)
from ..utils import (
    unified_strdate,
    determine_ext,
    int_or_none,
    parse_iso8601,
    parse_duration,
)


class NHLBaseInfoExtractor(InfoExtractor):
    @staticmethod
    def _fix_json(json_string):
        return json_string.replace('\\\'', '\'')

    def _real_extract_video(self, video_id):
        vid_parts = video_id.split(',')
        if len(vid_parts) == 3:
            video_id = '%s0%s%s-X-h' % (vid_parts[0][:4], vid_parts[1], vid_parts[2].rjust(4, '0'))
        json_url = 'http://video.nhl.com/videocenter/servlets/playlist?ids=%s&format=json' % video_id
        data = self._download_json(
            json_url, video_id, transform_source=self._fix_json)
        return self._extract_video(data[0])

    def _extract_video(self, info):
        video_id = info['id']
        self.report_extraction(video_id)

        initial_video_url = info['publishPoint']
        if info['formats'] == '1':
            parsed_url = compat_urllib_parse_urlparse(initial_video_url)
            filename, ext = os.path.splitext(parsed_url.path)
            path = '%s_sd%s' % (filename, ext)
            data = compat_urllib_parse_urlencode({
                'type': 'fvod',
                'path': compat_urlparse.urlunparse(parsed_url[:2] + (path,) + parsed_url[3:])
            })
            path_url = 'http://video.nhl.com/videocenter/servlets/encryptvideopath?' + data
            path_doc = self._download_xml(
                path_url, video_id, 'Downloading final video url')
            video_url = path_doc.find('path').text
        else:
            video_url = initial_video_url

        join = compat_urlparse.urljoin
        ret = {
            'id': video_id,
            'title': info['name'],
            'url': video_url,
            'description': info['description'],
            'duration': int(info['duration']),
            'thumbnail': join(join(video_url, '/u/'), info['bigImage']),
            'upload_date': unified_strdate(info['releaseDate'].split('.')[0]),
        }
        if video_url.startswith('rtmp:'):
            mobj = re.match(r'(?P<tc_url>rtmp://[^/]+/(?P<app>[a-z0-9/]+))/(?P<play_path>mp4:.*)', video_url)
            ret.update({
                'tc_url': mobj.group('tc_url'),
                'play_path': mobj.group('play_path'),
                'app': mobj.group('app'),
                'no_resume': True,
            })
        return ret


class NHLVideocenterIE(NHLBaseInfoExtractor):
    IE_NAME = 'nhl.com:videocenter'
    _VALID_URL = r'https?://video(?P<team>\.[^.]*)?\.nhl\.com/videocenter/(?:console|embed)?(?:\?(?:.*?[?&])?)(?:id|hlg|playlist)=(?P<id>[-0-9a-zA-Z,]+)'

    _TESTS = [{
        'url': 'http://video.canucks.nhl.com/videocenter/console?catid=6?id=453614',
        'md5': 'db704a4ea09e8d3988c85e36cc892d09',
        'info_dict': {
            'id': '453614',
            'ext': 'mp4',
            'title': 'Quick clip: Weise 4-3 goal vs Flames',
            'description': 'Dale Weise scores his first of the season to put the Canucks up 4-3.',
            'duration': 18,
            'upload_date': '20131006',
        },
    }, {
        'url': 'http://video.nhl.com/videocenter/console?id=2014020024-628-h',
        'md5': 'd22e82bc592f52d37d24b03531ee9696',
        'info_dict': {
            'id': '2014020024-628-h',
            'ext': 'mp4',
            'title': 'Alex Galchenyuk Goal on Ray Emery (14:40/3rd)',
            'description': 'Home broadcast - Montreal Canadiens at Philadelphia Flyers - October 11, 2014',
            'duration': 0,
            'upload_date': '20141011',
        },
    }, {
        'url': 'http://video.mapleleafs.nhl.com/videocenter/console?id=58665&catid=802',
        'md5': 'c78fc64ea01777e426cfc202b746c825',
        'info_dict': {
            'id': '58665',
            'ext': 'flv',
            'title': 'Classic Game In Six - April 22, 1979',
            'description': 'It was the last playoff game for the Leafs in the decade, and the last time the Leafs and Habs played in the playoffs. Great game, not a great ending.',
            'duration': 400,
            'upload_date': '20100129'
        },
    }, {
        'url': 'http://video.flames.nhl.com/videocenter/console?id=630616',
        'only_matching': True,
    }, {
        'url': 'http://video.nhl.com/videocenter/?id=736722',
        'only_matching': True,
    }, {
        'url': 'http://video.nhl.com/videocenter/console?hlg=20142015,2,299&lang=en',
        'md5': '076fcb88c255154aacbf0a7accc3f340',
        'info_dict': {
            'id': '2014020299-X-h',
            'ext': 'mp4',
            'title': 'Penguins at Islanders / Game Highlights',
            'description': 'Home broadcast - Pittsburgh Penguins at New York Islanders - November 22, 2014',
            'duration': 268,
            'upload_date': '20141122',
        }
    }, {
        'url': 'http://video.oilers.nhl.com/videocenter/console?id=691469&catid=4',
        'info_dict': {
            'id': '691469',
            'ext': 'mp4',
            'title': 'RAW | Craig MacTavish Full Press Conference',
            'description': 'Oilers GM Craig MacTavish addresses the media at Rexall Place on Friday.',
            'upload_date': '20141205',
        },
        'params': {
            'skip_download': True,  # Requires rtmpdump
        }
    }, {
        'url': 'http://video.nhl.com/videocenter/embed?playlist=836127',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._real_extract_video(video_id)


class NHLNewsIE(NHLBaseInfoExtractor):
    IE_NAME = 'nhl.com:news'
    IE_DESC = 'NHL news'
    _VALID_URL = r'https?://(?:.+?\.)?nhl\.com/(?:ice|club)/news\.html?(?:\?(?:.*?[?&])?)id=(?P<id>[-0-9a-zA-Z]+)'

    _TESTS = [{
        'url': 'http://www.nhl.com/ice/news.htm?id=750727',
        'md5': '4b3d1262e177687a3009937bd9ec0be8',
        'info_dict': {
            'id': '736722',
            'ext': 'mp4',
            'title': 'Cal Clutterbuck has been fined $2,000',
            'description': 'md5:45fe547d30edab88b23e0dd0ab1ed9e6',
            'duration': 37,
            'upload_date': '20150128',
        },
    }, {
        # iframe embed
        'url': 'http://sabres.nhl.com/club/news.htm?id=780189',
        'md5': '9f663d1c006c90ac9fb82777d4294e12',
        'info_dict': {
            'id': '836127',
            'ext': 'mp4',
            'title': 'Morning Skate: OTT vs. BUF (9/23/15)',
            'description': "Brian Duff chats with Tyler Ennis prior to Buffalo's first preseason home game.",
            'duration': 93,
            'upload_date': '20150923',
        },
    }]

    def _real_extract(self, url):
        news_id = self._match_id(url)
        webpage = self._download_webpage(url, news_id)
        video_id = self._search_regex(
            [r'pVid(\d+)', r"nlid\s*:\s*'(\d+)'",
             r'<iframe[^>]+src=["\']https?://video.*?\.nhl\.com/videocenter/embed\?.*\bplaylist=(\d+)'],
            webpage, 'video id')
        return self._real_extract_video(video_id)


class NHLVideocenterCategoryIE(NHLBaseInfoExtractor):
    IE_NAME = 'nhl.com:videocenter:category'
    IE_DESC = 'NHL videocenter category'
    _VALID_URL = r'https?://video\.(?P<team>[^.]*)\.nhl\.com/videocenter/(console\?[^(id=)]*catid=(?P<catid>[0-9]+)(?![&?]id=).*?)?$'
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

        data = compat_urllib_parse_urlencode({
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
            self._downloader.report_warning('Got an empty response, trying '
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


class NHLIE(InfoExtractor):
    IE_NAME = 'nhl.com'
    _VALID_URL = r'https?://(?:www\.)?nhl\.com/([^/]+/)*c-(?P<id>\d+)'
    _TESTS = [{
        # type=video
        'url': 'https://www.nhl.com/video/anisimov-cleans-up-mess/t-277752844/c-43663503',
        'md5': '0f7b9a8f986fb4b4eeeece9a56416eaf',
        'info_dict': {
            'id': '43663503',
            'ext': 'mp4',
            'title': 'Anisimov cleans up mess',
            'description': 'md5:a02354acdfe900e940ce40706939ca63',
            'timestamp': 1461288600,
            'upload_date': '20160422',
        },
    }, {
        # type=article
        'url': 'https://www.nhl.com/news/dennis-wideman-suspended/c-278258934',
        'md5': '1f39f4ea74c1394dea110699a25b366c',
        'info_dict': {
            'id': '40784403',
            'ext': 'mp4',
            'title': 'Wideman suspended by NHL',
            'description': 'Flames defenseman Dennis Wideman was banned 20 games for violation of Rule 40 (Physical Abuse of Officials)',
            'upload_date': '20160204',
            'timestamp': 1454544904,
        },
    }]

    def _real_extract(self, url):
        tmp_id = self._match_id(url)
        video_data = self._download_json(
            'https://nhl.bamcontent.com/nhl/id/v1/%s/details/web-v1.json' % tmp_id,
            tmp_id)
        if video_data.get('type') == 'article':
            video_data = video_data['media']

        video_id = compat_str(video_data['id'])
        title = video_data['title']

        formats = []
        for playback in video_data.get('playbacks', []):
            playback_url = playback.get('url')
            if not playback_url:
                continue
            ext = determine_ext(playback_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    playback_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=playback.get('name', 'hls'), fatal=False))
            else:
                height = int_or_none(playback.get('height'))
                formats.append({
                    'format_id': playback.get('name', 'http' + ('-%dp' % height if height else '')),
                    'url': playback_url,
                    'width': int_or_none(playback.get('width')),
                    'height': height,
                })
        self._sort_formats(formats, ('preference', 'width', 'height', 'tbr', 'format_id'))

        thumbnails = []
        for thumbnail_id, thumbnail_data in video_data.get('image', {}).get('cuts', {}).items():
            thumbnail_url = thumbnail_data.get('src')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'id': thumbnail_id,
                'url': thumbnail_url,
                'width': int_or_none(thumbnail_data.get('width')),
                'height': int_or_none(thumbnail_data.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'timestamp': parse_iso8601(video_data.get('date')),
            'duration': parse_duration(video_data.get('duration')),
            'thumbnails': thumbnails,
            'formats': formats,
        }
