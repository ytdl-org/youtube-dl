# coding: utf-8
from __future__ import unicode_literals

import re

from .theplatform import ThePlatformIE
from ..utils import (
    extract_attributes,
    ExtractorError,
    int_or_none,
    smuggle_url,
    update_url_query,
)
from ..compat import (
    compat_urlparse,
)


class AENetworksBaseIE(ThePlatformIE):
    _THEPLATFORM_KEY = 'crazyjava'
    _THEPLATFORM_SECRET = 's3cr3t'

    def _extract_aen_smil(self, smil_url, video_id, auth=None):
        query = {'mbr': 'true'}
        if auth:
            query['auth'] = auth
        TP_SMIL_QUERY = [{
            'assetTypes': 'high_video_ak',
            'switch': 'hls_high_ak'
        }, {
            'assetTypes': 'high_video_s3'
        }, {
            'assetTypes': 'high_video_s3',
            'switch': 'hls_ingest_fastly'
        }]
        formats = []
        subtitles = {}
        last_e = None
        for q in TP_SMIL_QUERY:
            q.update(query)
            m_url = update_url_query(smil_url, q)
            m_url = self._sign_url(m_url, self._THEPLATFORM_KEY, self._THEPLATFORM_SECRET)
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    m_url, video_id, 'Downloading %s SMIL data' % (q.get('switch') or q['assetTypes']))
            except ExtractorError as e:
                last_e = e
                continue
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        if last_e and not formats:
            raise last_e
        self._sort_formats(formats)
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }


class AENetworksIE(AENetworksBaseIE):
    IE_NAME = 'aenetworks'
    IE_DESC = 'A+E Networks: A&E, Lifetime, History.com, FYI Network and History Vault'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?P<domain>
                            (?:history(?:vault)?|aetv|mylifetime|lifetimemovieclub)\.com|
                            fyi\.tv
                        )/
                        (?:
                            shows/(?P<show_path>[^/]+(?:/[^/]+){0,2})|
                            movies/(?P<movie_display_id>[^/]+)(?:/full-movie)?|
                            specials/(?P<special_display_id>[^/]+)/(?:full-special|preview-)|
                            collections/[^/]+/(?P<collection_display_id>[^/]+)
                        )
                    '''
    _TESTS = [{
        'url': 'http://www.history.com/shows/mountain-men/season-1/episode-1',
        'info_dict': {
            'id': '22253814',
            'ext': 'mp4',
            'title': 'Winter is Coming',
            'description': 'md5:641f424b7a19d8e24f26dea22cf59d74',
            'timestamp': 1338306241,
            'upload_date': '20120529',
            'uploader': 'AENE-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
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
    }, {
        'url': 'https://www.lifetimemovieclub.com/movies/a-killer-among-us',
        'only_matching': True
    }, {
        'url': 'http://www.history.com/specials/sniper-into-the-kill-zone/full-special',
        'only_matching': True
    }, {
        'url': 'https://www.historyvault.com/collections/america-the-story-of-us/westward',
        'only_matching': True
    }, {
        'url': 'https://www.aetv.com/specials/hunting-jonbenets-killer-the-untold-story/preview-hunting-jonbenets-killer-the-untold-story',
        'only_matching': True
    }]
    _DOMAIN_TO_REQUESTOR_ID = {
        'history.com': 'HISTORY',
        'aetv.com': 'AETV',
        'mylifetime.com': 'LIFETIME',
        'lifetimemovieclub.com': 'LIFETIMEMOVIECLUB',
        'fyi.tv': 'FYI',
    }

    def _real_extract(self, url):
        domain, show_path, movie_display_id, special_display_id, collection_display_id = re.match(self._VALID_URL, url).groups()
        display_id = show_path or movie_display_id or special_display_id or collection_display_id
        webpage = self._download_webpage(url, display_id, headers=self.geo_verification_headers())
        if show_path:
            url_parts = show_path.split('/')
            url_parts_len = len(url_parts)
            if url_parts_len == 1:
                entries = []
                for season_url_path in re.findall(r'(?s)<li[^>]+data-href="(/shows/%s/season-\d+)"' % url_parts[0], webpage):
                    entries.append(self.url_result(
                        compat_urlparse.urljoin(url, season_url_path), 'AENetworks'))
                if entries:
                    return self.playlist_result(
                        entries, self._html_search_meta('aetn:SeriesId', webpage),
                        self._html_search_meta('aetn:SeriesTitle', webpage))
                else:
                    # single season
                    url_parts_len = 2
            if url_parts_len == 2:
                entries = []
                for episode_item in re.findall(r'(?s)<[^>]+class="[^"]*(?:episode|program)-item[^"]*"[^>]*>', webpage):
                    episode_attributes = extract_attributes(episode_item)
                    episode_url = compat_urlparse.urljoin(
                        url, episode_attributes['data-canonical'])
                    entries.append(self.url_result(
                        episode_url, 'AENetworks',
                        episode_attributes.get('data-videoid') or episode_attributes.get('data-video-id')))
                return self.playlist_result(
                    entries, self._html_search_meta('aetn:SeasonId', webpage))

        video_id = self._html_search_meta('aetn:VideoID', webpage)
        media_url = self._search_regex(
            [r"media_url\s*=\s*'(?P<url>[^']+)'",
             r'data-media-url=(?P<url>(?:https?:)?//[^\s>]+)',
             r'data-media-url=(["\'])(?P<url>(?:(?!\1).)+?)\1'],
            webpage, 'video url', group='url')
        theplatform_metadata = self._download_theplatform_metadata(self._search_regex(
            r'https?://link\.theplatform\.com/s/([^?]+)', media_url, 'theplatform_path'), video_id)
        info = self._parse_theplatform_metadata(theplatform_metadata)
        auth = None
        if theplatform_metadata.get('AETN$isBehindWall'):
            requestor_id = self._DOMAIN_TO_REQUESTOR_ID[domain]
            resource = self._get_mvpd_resource(
                requestor_id, theplatform_metadata['title'],
                theplatform_metadata.get('AETN$PPL_pplProgramId') or theplatform_metadata.get('AETN$PPL_pplProgramId_OLD'),
                theplatform_metadata['ratings'][0]['rating'])
            auth = self._extract_mvpd_auth(
                url, video_id, requestor_id, resource)
        info.update(self._search_json_ld(webpage, video_id, fatal=False))
        info.update(self._extract_aen_smil(media_url, video_id, auth))
        return info


class HistoryTopicIE(AENetworksBaseIE):
    IE_NAME = 'history:topic'
    IE_DESC = 'History.com Topic'
    _VALID_URL = r'https?://(?:www\.)?history\.com/topics/[^/]+/(?P<id>[\w+-]+?)-video'
    _TESTS = [{
        'url': 'https://www.history.com/topics/valentines-day/history-of-valentines-day-video',
        'info_dict': {
            'id': '40700995724',
            'ext': 'mp4',
            'title': "History of Valentine’s Day",
            'description': 'md5:7b57ea4829b391995b405fa60bd7b5f7',
            'timestamp': 1375819729,
            'upload_date': '20130806',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['ThePlatform'],
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
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'<phoenix-iframe[^>]+src="[^"]+\btpid=(\d+)', webpage, 'tpid')
        result = self._download_json(
            'https://feeds.video.aetnd.com/api/v2/history/videos',
            video_id, query={'filter[id]': video_id})['results'][0]
        title = result['title']
        info = self._extract_aen_smil(result['publicUrl'], video_id)
        info.update({
            'title': title,
            'description': result.get('description'),
            'duration': int_or_none(result.get('duration')),
            'timestamp': int_or_none(result.get('added'), 1000),
        })
        return info
