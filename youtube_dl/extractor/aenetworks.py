from __future__ import unicode_literals

import re

from .theplatform import ThePlatformIE
from ..utils import (
    smuggle_url,
    update_url_query,
    unescapeHTML,
    extract_attributes,
    get_element_by_attribute,
)
from ..compat import (
    compat_urlparse,
)


class AENetworksBaseIE(ThePlatformIE):
    _THEPLATFORM_KEY = 'crazyjava'
    _THEPLATFORM_SECRET = 's3cr3t'


class AENetworksIE(AENetworksBaseIE):
    IE_NAME = 'aenetworks'
    IE_DESC = 'A+E Networks: A&E, Lifetime, History.com, FYI Network'
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>(?:history|aetv|mylifetime)\.com|fyi\.tv)/(?:shows/(?P<show_path>[^/]+(?:/[^/]+){0,2})|movies/(?P<movie_display_id>[^/]+)/full-movie)'
    _TESTS = [{
        'url': 'http://www.history.com/shows/mountain-men/season-1/episode-1',
        'md5': 'a97a65f7e823ae10e9244bc5433d5fe6',
        'info_dict': {
            'id': '22253814',
            'ext': 'mp4',
            'title': 'Winter Is Coming',
            'description': 'md5:641f424b7a19d8e24f26dea22cf59d74',
            'timestamp': 1338306241,
            'upload_date': '20120529',
            'uploader': 'AENE-NEW',
        },
        'add_ie': ['ThePlatform'],
    }, {
        'url': 'http://www.history.com/shows/ancient-aliens/season-1',
        'info_dict': {
            'id': '71889446852',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'http://www.mylifetime.com/shows/atlanta-plastic',
        'info_dict': {
            'id': 'SERIES4317',
            'title': 'Atlanta Plastic',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'http://www.aetv.com/shows/duck-dynasty/season-9/episode-1',
        'only_matching': True
    }, {
        'url': 'http://www.fyi.tv/shows/tiny-house-nation/season-1/episode-8',
        'only_matching': True
    }, {
        'url': 'http://www.mylifetime.com/shows/project-runway-junior/season-1/episode-6',
        'only_matching': True
    }, {
        'url': 'http://www.mylifetime.com/movies/center-stage-on-pointe/full-movie',
        'only_matching': True
    }]
    _DOMAIN_TO_REQUESTOR_ID = {
        'history.com': 'HISTORY',
        'aetv.com': 'AETV',
        'mylifetime.com': 'LIFETIME',
        'fyi.tv': 'FYI',
    }

    def _real_extract(self, url):
        domain, show_path, movie_display_id = re.match(self._VALID_URL, url).groups()
        display_id = show_path or movie_display_id
        webpage = self._download_webpage(url, display_id)
        if show_path:
            url_parts = show_path.split('/')
            url_parts_len = len(url_parts)
            if url_parts_len == 1:
                entries = []
                for season_url_path in re.findall(r'(?s)<li[^>]+data-href="(/shows/%s/season-\d+)"' % url_parts[0], webpage):
                    entries.append(self.url_result(
                        compat_urlparse.urljoin(url, season_url_path), 'AENetworks'))
                return self.playlist_result(
                    entries, self._html_search_meta('aetn:SeriesId', webpage),
                    self._html_search_meta('aetn:SeriesTitle', webpage))
            elif url_parts_len == 2:
                entries = []
                for episode_item in re.findall(r'(?s)<div[^>]+class="[^"]*episode-item[^"]*"[^>]*>', webpage):
                    episode_attributes = extract_attributes(episode_item)
                    episode_url = compat_urlparse.urljoin(
                        url, episode_attributes['data-canonical'])
                    entries.append(self.url_result(
                        episode_url, 'AENetworks',
                        episode_attributes['data-videoid']))
                return self.playlist_result(
                    entries, self._html_search_meta('aetn:SeasonId', webpage))

        query = {
            'mbr': 'true',
            'assetTypes': 'high_video_s3'
        }
        video_id = self._html_search_meta('aetn:VideoID', webpage)
        media_url = self._search_regex(
            r"media_url\s*=\s*'([^']+)'", webpage, 'video url')
        theplatform_metadata = self._download_theplatform_metadata(self._search_regex(
            r'https?://link.theplatform.com/s/([^?]+)', media_url, 'theplatform_path'), video_id)
        info = self._parse_theplatform_metadata(theplatform_metadata)
        if theplatform_metadata.get('AETN$isBehindWall'):
            requestor_id = self._DOMAIN_TO_REQUESTOR_ID[domain]
            resource = self._get_mvpd_resource(
                requestor_id, theplatform_metadata['title'],
                theplatform_metadata.get('AETN$PPL_pplProgramId') or theplatform_metadata.get('AETN$PPL_pplProgramId_OLD'),
                theplatform_metadata['ratings'][0]['rating'])
            query['auth'] = self._extract_mvpd_auth(
                url, video_id, requestor_id, resource)
        info.update(self._search_json_ld(webpage, video_id, fatal=False))
        media_url = update_url_query(media_url, query)
        media_url = self._sign_url(media_url, self._THEPLATFORM_KEY, self._THEPLATFORM_SECRET)
        formats, subtitles = self._extract_theplatform_smil(media_url, video_id)
        self._sort_formats(formats)
        info.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        })
        return info


class HistoryTopicIE(AENetworksBaseIE):
    IE_NAME = 'history:topic'
    IE_DESC = 'History.com Topic'
    _VALID_URL = r'https?://(?:www\.)?history\.com/topics/(?:[^/]+/)?(?P<topic_id>[^/]+)(?:/[^/]+(?:/(?P<video_display_id>[^/?#]+))?)?'
    _TESTS = [{
        'url': 'http://www.history.com/topics/valentines-day/history-of-valentines-day/videos/bet-you-didnt-know-valentines-day?m=528e394da93ae&s=undefined&f=1&free=false',
        'info_dict': {
            'id': '40700995724',
            'ext': 'mp4',
            'title': "Bet You Didn't Know: Valentine's Day",
            'description': 'md5:7b57ea4829b391995b405fa60bd7b5f7',
            'timestamp': 1375819729,
            'upload_date': '20130806',
            'uploader': 'AENE-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['ThePlatform'],
    }, {
        'url': 'http://www.history.com/topics/world-war-i/world-war-i-history/videos',
        'info_dict':
        {
            'id': 'world-war-i-history',
            'title': 'World War I History',
        },
        'playlist_mincount': 23,
    }, {
        'url': 'http://www.history.com/topics/world-war-i-history/videos',
        'only_matching': True,
    }, {
        'url': 'http://www.history.com/topics/world-war-i/world-war-i-history',
        'only_matching': True,
    }, {
        'url': 'http://www.history.com/topics/world-war-i/world-war-i-history/speeches',
        'only_matching': True,
    }]

    def theplatform_url_result(self, theplatform_url, video_id, query):
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': smuggle_url(
                update_url_query(theplatform_url, query),
                {
                    'sig': {
                        'key': self._THEPLATFORM_KEY,
                        'secret': self._THEPLATFORM_SECRET,
                    },
                    'force_smil_url': True
                }),
            'ie_key': 'ThePlatform',
        }

    def _real_extract(self, url):
        topic_id, video_display_id = re.match(self._VALID_URL, url).groups()
        if video_display_id:
            webpage = self._download_webpage(url, video_display_id)
            release_url, video_id = re.search(r"_videoPlayer.play\('([^']+)'\s*,\s*'[^']+'\s*,\s*'(\d+)'\)", webpage).groups()
            release_url = unescapeHTML(release_url)

            return self.theplatform_url_result(
                release_url, video_id, {
                    'mbr': 'true',
                    'switch': 'hls',
                    'assetTypes': 'high_video_ak',
                })
        else:
            webpage = self._download_webpage(url, topic_id)
            entries = []
            for episode_item in re.findall(r'<a.+?data-release-url="[^"]+"[^>]*>', webpage):
                video_attributes = extract_attributes(episode_item)
                entries.append(self.theplatform_url_result(
                    video_attributes['data-release-url'], video_attributes['data-id'], {
                        'mbr': 'true',
                        'switch': 'hls',
                        'assetTypes': 'high_video_ak',
                    }))
            return self.playlist_result(entries, topic_id, get_element_by_attribute('class', 'show-title', webpage))
