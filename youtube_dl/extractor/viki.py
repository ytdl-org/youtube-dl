from __future__ import unicode_literals

import re

from ..compat import (
    compat_urlparse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate,
    US_RATINGS,
    determine_ext,
    mimetype2ext,
)
from .common import InfoExtractor


class VikiIE(InfoExtractor):
    IE_NAME = 'viki'

    # iPad2
    _USER_AGENT = 'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'

    _VALID_URL = r'https?://(?:www\.)?viki\.com/videos/(?P<id>[0-9]+v)'
    _TESTS = [{
        'url': 'http://www.viki.com/videos/1023585v-heirs-episode-14',
        'info_dict': {
            'id': '1023585v',
            'ext': 'mp4',
            'title': 'Heirs Episode 14',
            'uploader': 'SBS',
            'description': 'md5:c4b17b9626dd4b143dcc4d855ba3474e',
            'upload_date': '20131121',
            'age_limit': 13,
        },
        'skip': 'Blocked in the US',
    }, {
        'url': 'http://www.viki.com/videos/1067139v-the-avengers-age-of-ultron-press-conference',
        'md5': 'ca6493e6f0a6ec07da9aa8d6304b4b2c',
        'info_dict': {
            'id': '1067139v',
            'ext': 'mp4',
            'description': 'md5:d70b2f9428f5488321bfe1db10d612ea',
            'upload_date': '20150430',
            'title': '\'The Avengers: Age of Ultron\' Press Conference',
        }
    }, {
        'url': 'http://www.viki.com/videos/1048879v-ankhon-dekhi',
        'info_dict': {
            'id': '1048879v',
            'ext': 'mp4',
            'upload_date': '20140820',
            'description': 'md5:54ff56d51bdfc7a30441ec967394e91c',
            'title': 'Ankhon Dekhi',
        },
        'params': {
            # requires ffmpeg
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        uploader_m = re.search(
            r'<strong>Broadcast Network: </strong>\s*([^<]*)<', webpage)
        if uploader_m is None:
            uploader = None
        else:
            uploader = uploader_m.group(1).strip()

        rating_str = self._html_search_regex(
            r'<strong>Rating: </strong>\s*([^<]*)<', webpage,
            'rating information', default='').strip()
        age_limit = US_RATINGS.get(rating_str)

        req = compat_urllib_request.Request(
            'http://www.viki.com/player5_fragment/%s?action=show&controller=videos' % video_id)
        req.add_header('User-Agent', self._USER_AGENT)
        info_webpage = self._download_webpage(
            req, video_id, note='Downloading info page')
        err_msg = self._html_search_regex(r'<div[^>]+class="video-error[^>]+>(.+)</div>', info_webpage, 'error message', default=None)
        if err_msg:
            if 'not available in your region' in err_msg:
                raise ExtractorError(
                    'Video %s is blocked from your location.' % video_id,
                    expected=True)
            else:
                raise ExtractorError('Viki said: %s %s' % (err_msg, url))
        mobj = re.search(
            r'<source[^>]+type="(?P<mime_type>[^"]+)"[^>]+src="(?P<url>[^"]+)"', info_webpage)
        if not mobj:
            raise ExtractorError('Unable to find video URL')
        video_url = unescapeHTML(mobj.group('url'))
        video_ext = mimetype2ext(mobj.group('mime_type'))

        if determine_ext(video_url) == 'm3u8':
            formats = self._extract_m3u8_formats(
                video_url, video_id, ext=video_ext)
        else:
            formats = [{
                'url': video_url,
                'ext': video_ext,
            }]

        upload_date_str = self._html_search_regex(
            r'"created_at":"([^"]+)"', info_webpage, 'upload date')
        upload_date = (
            unified_strdate(upload_date_str)
            if upload_date_str is not None
            else None
        )

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, info_webpage)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
            'age_limit': age_limit,
            'uploader': uploader,
            'subtitles': video_subtitles,
            'upload_date': upload_date,
        }

    def _get_subtitles(self, video_id, info_webpage):
        res = {}
        for sturl_html in re.findall(r'<track src="([^"]+)"', info_webpage):
            sturl = unescapeHTML(sturl_html)
            m = re.search(r'/(?P<lang>[a-z]+)\.vtt', sturl)
            if not m:
                continue
            res[m.group('lang')] = [{
                'url': compat_urlparse.urljoin('http://www.viki.com', sturl),
                'ext': 'vtt',
            }]
        return res


class VikiChannelIE(InfoExtractor):
    IE_NAME = 'viki:channel'
    _VALID_URL = r'https?://(?:www\.)?viki\.com/tv/(?P<id>[0-9]+c)'
    _TESTS = [{
        'url': 'http://www.viki.com/tv/50c-boys-over-flowers',
        'info_dict': {
            'id': '50c',
            'title': 'Boys Over Flowers',
            'description': 'md5:ecd3cff47967fe193cff37c0bec52790',
        },
        'playlist_count': 70,
    }, {
        'url': 'http://www.viki.com/tv/1354c-poor-nastya-complete',
        'info_dict': {
            'id': '1354c',
            'title': 'Poor Nastya [COMPLETE]',
            'description': 'md5:05bf5471385aa8b21c18ad450e350525',
        },
        'playlist_count': 127,
    }]
    _API_BASE = 'http://api.viki.io/v4/containers'
    _APP = '100000a'
    _PER_PAGE = 25

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        channel = self._download_json(
            '%s/%s.json?app=%s' % (self._API_BASE, channel_id, self._APP),
            channel_id, 'Downloading channel JSON')

        titles = channel['titles']
        title = titles.get('en') or titles[titles.keys()[0]]

        descriptions = channel['descriptions']
        description = descriptions.get('en') or descriptions[descriptions.keys()[0]]

        entries = []
        for video_type in ('episodes', 'clips'):
            page_url = '%s/%s/%s.json?app=%s&per_page=%d&sort=number&direction=asc&with_paging=true&page=1' % (self._API_BASE, channel_id, video_type, self._APP, self._PER_PAGE)
            while page_url:
                page = self._download_json(
                    page_url, channel_id,
                    'Downloading %s JSON page #%s'
                    % (video_type, re.search(r'[?&]page=([0-9]+)', page_url).group(1)))
                for video in page['response']:
                    video_id = video['id']
                    entries.append(self.url_result(
                        'http://www.viki.com/videos/%s' % video_id, 'Viki', video_id))
                page_url = page['pagination']['next']

        return self.playlist_result(entries, channel_id, title, description)
