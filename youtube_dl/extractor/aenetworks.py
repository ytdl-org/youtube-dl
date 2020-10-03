# coding: utf-8
from __future__ import unicode_literals

import json
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

    def _parse_theplatform_metadata(self, info):
        metadata = super()._parse_theplatform_metadata(info)
        metadata['season_number'] = int(info.get('AETN$season'))
        metadata['episode_number'] = int(info.get('AETN$episode'))
        metadata['series'] = info.get('AETN$seriesNameGlobal')
        return metadata

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
                        (?:(?P<subdomain>www|play)\.)?
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
    _GRAPHQL_QUERY = """
fragment video on Video {
  publicUrl
}

query getUserVideo($videoId: ID!) {
  video(id: $videoId) {
    ...video
  }
}
"""

    _TESTS = [{
        'url': 'http://www.history.com/shows/mountain-men/season-1/episode-1',
        'info_dict': {
            'id': '22253814',
            'ext': 'mp4',
            'series': 'Mountain Men',
            'season_number': 1,
            'episode_number': 1,
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
        'url': 'http://play.history.com/shows/mountain-men/season-1/episode-1',
        'info_dict': {
            'id': '22253814',
            'ext': 'mp4',
            'series': 'Mountain Men',
            'season_number': 1,
            'episode_number': 1,
            'title': 'Winter Is Coming',
            'description': 'md5:a40e370925074260b1c8a633c632c63a',
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
            'title': 'Ancient Aliens'
        },
        'playlist_mincount': 5,
    }, {
        'url': 'http://www.mylifetime.com/shows/marrying-millions',
        'info_dict': {
            'id': 'SERIES6093',
            'title': 'Marrying Millions',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'http://www.mylifetime.com/shows/marrying-millions/season-1',
        'info_dict': {
            'id': '269343782619',
            'title': 'Marrying Millions',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://play.mylifetime.com/shows/marrying-millions/season-1',
        'info_dict': {
            'id': 'SERIES6093',
            'title': 'Marrying Millions',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://play.mylifetime.com/shows/marrying-millions',
        'info_dict': {
            'id': 'SERIES6093',
            'title': 'Marrying Millions',
        },
        'playlist_mincount': 11,
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

    def _extract_playlist(self, url, webpage, display_id, subdomain, url_parts):
        # The "play" is pretty distinct from the normal sites, however, it contains all the data we need in a JSON blob.
        if subdomain == 'play':
            series_id = self._search_regex(r'showid/(SERIES[0-9]+)', webpage, 'series id')
            season_num = int_or_none(self._search_regex(r'/season-([0-9]+)/?', url, 'season number', fatal=False, default=None))
            show_data = self._parse_json(
                self._search_regex(r'(?s)<script[^>]+id="__NEXT_DATA__"[^>]*>(.+?)</script', webpage, 'show data'),
                series_id, fatal=True)
            if show_data:
                apolloState = show_data.get('props', {}).get('apolloState', {})
                entries = []
                for key, episode in apolloState.items():
                    if not key.startswith('Episode:') or series_id != episode.get('seriesId'):
                        continue
                    # If a season number was specified in the URL, filter out any episodes that don't match.
                    if season_num and season_num != episode.get('tvSeasonNumber'):
                        continue
                    episode_url = compat_urlparse.urljoin(url, episode.get('canonical'))
                    entries.append(self.url_result(episode_url, 'AENetworks', episode.get('id'), episode.get('title')))
                series_name = apolloState.get('Series:%s' % series_id, {}).get('title')
                return self.playlist_result(entries, series_id, series_name)
        else:
            series_title = self._html_search_meta('aetn:SeriesTitle', webpage)
            url_parts_len = len(url_parts)
            if url_parts_len == 1:
                entries = []
                for season_url_path in re.findall(r'(?s)<a[^>]+href="(/shows/%s/season-\d+)"' % url_parts[0], webpage):
                    entries.append(self.url_result(
                        compat_urlparse.urljoin(url, season_url_path), 'AENetworks'))
                if entries:
                    return self.playlist_result(
                        entries, self._html_search_meta('aetn:SeriesId', webpage), series_title)
                raise ExtractorError('Failed to extract seasons for show: %s' % url_parts[0])
            if url_parts_len == 2:
                entries = []
                for episode_item in re.findall(r'(?s)<[^>]+data-episodetype[^>]*>', webpage):
                    episode_attributes = extract_attributes(episode_item)
                    episode_url = compat_urlparse.urljoin(
                        url, episode_attributes['data-canonical'])
                    video_id = episode_attributes.get('data-videoid') or episode_attributes.get('data-video-id')
                    episode_title = episode_attributes.get('aria-label')
                    entries.append(self.url_result(episode_url, 'AENetworks', video_id, episode_title))
                return self.playlist_result(
                    entries, self._html_search_meta('aetn:SeasonId', webpage), series_title)
        raise ExtractorError('Failed to extract playlist', video_id=display_id)

    def _real_extract(self, url):
        subdomain, domain, show_path, movie_display_id, special_display_id, collection_display_id = re.match(self._VALID_URL, url).groups()
        display_id = show_path or movie_display_id or special_display_id or collection_display_id
        webpage = self._download_webpage(url, display_id, headers=self.geo_verification_headers())

        if show_path:
            url_parts = show_path.split('/')
            # If there's only the show name and/or season number then we'll need to extract a playlist.
            if len(url_parts) < 3:
                return self._extract_playlist(url, webpage, display_id, subdomain, url_parts)

        requestor_id = self._DOMAIN_TO_REQUESTOR_ID[domain]
        video_id = self._html_search_meta(['videoId', 'aetn:VideoID'], webpage)
        # Make a GraphQL query to get the episode URL as they no longer directly embed it in the response webpage.
        video_data = self._download_json(
            'https://yoga.appsvcs.aetnd.com/graphql?brand=%s&mode=live&platform=web' % (requestor_id.lower()), video_id,
            data=json.dumps(
                {
                    'operationName': 'getUserVideo',
                    'variables': {'videoId': video_id},
                    'query': self._GRAPHQL_QUERY,
                }).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        media_url = video_data.get('data', {}).get('video', {}).get('publicUrl')
        if not media_url:
            raise ExtractorError('Failed to extract media URL', video_id=video_id)
        theplatform_metadata = self._download_theplatform_metadata(self._search_regex(
            r'https?://link\.theplatform\.com/s/([^?]+)', media_url, 'theplatform_path'), video_id)
        info = self._parse_theplatform_metadata(theplatform_metadata)
        auth = None
        if theplatform_metadata.get('AETN$isBehindWall'):
            resource = self._get_mvpd_resource(
                requestor_id, theplatform_metadata['title'],
                theplatform_metadata.get('AETN$PPL_pplProgramId') or theplatform_metadata.get('AETN$PPL_pplProgramId_OLD'),
                theplatform_metadata['ratings'][0]['rating'])
            auth = self._extract_mvpd_auth(
                url, video_id, requestor_id, resource)
        # JSON-LD data isn't present on the play subdomain webpages.
        if subdomain != 'play':
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
