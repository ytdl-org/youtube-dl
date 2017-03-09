# coding: utf-8
from __future__ import unicode_literals

import re
from datetime import datetime

from .turner import TurnerBaseIE
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    determine_ext,
)


class AdultSwimIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?adultswim\.com/videos/(?P<is_playlist>playlists/)?(?P<show_path>[^/]+)/(?P<episode_path>[^/?#]+)/?'

    _TESTS = [{
        'url': 'http://www.adultswim.com/videos/toonami/intruder-ii-episode-1/',
        'info_dict': {
            'id': 'RWFLm_htTKOW-7ZuCfzluQ',
            'ext': 'mp4',
            'title': 'Intruder II - Episode 1',
            'description': 'Watch the first epic episode of Intruder II. This is just the beginning.',
            'duration': 148,
            'series': 'Toonami',
            'season_number': 7,
            'episode_number': 1,
            'episode': 'Intruder II - Episode 1',
            'timestamp': 1448372637,
            'upload_date': '20151124',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': [
            'Failed to download m3u8 information: HTTP Error 403: Forbidden',
            'Unable to download f4m manifest'
        ],
    }, {
        'url': 'http://www.adultswim.com/videos/playlists/tina-belcher-butt-toucher?b=bobs_burgers',
        'info_dict': {
            'id': 'TUBMfnpdTYG_NdBueJX-Hg',
            'ext': 'flv',
            'title': 'Up My Butt',
            'description': 'A talking manatee makes Gene\'s pants tight.',
            'duration': 83.43,
            'series': 'Bob\'s Burgers',
            'season_number': None,
            'episode_number': None,
            'episode': 'Up My Butt',
            'timestamp': 1410559714,
            'upload_date': '20140912',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    },{
        'url': 'http://adultswim.com/videos/rick-and-morty/pilot',
        'info_dict': {
            'id': 'rQxZvXQ4ROaSOqq-or2Mow',
            'ext': 'mp4',
            'title': 'Pilot',
            'description': 'Rick moves in with his daughter\'s family and establishes himself as a bad influence on his grandson, Morty. ',
            'duration': 1321.004,
            'series': 'Rick and Morty',
            'season_number': 1,
            'episode_number': 1,
            'episode': 'Pilot',
            'timestamp': 1486592997,
            'upload_date': '20170208',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': [
            'Unable to download JSON metadata: HTTP Error 401'
        ],
        'skip': 'Requires a cable provider login',
    }]

    # Use the Adult Swim api (v2) for extracting all metadata about a video in a
    # friendly JSON format. Incudes video information, strea, closed captons, etc
    #
    # List of api keys:
    # Show info: http://www.adultswim.com/videos/app/show/{video_id}
    # Episode info: http://www.adultswim.com/videos/app/video/{video_id}
    #
    # Video api
    # http://www.adultswim.com/videos/api/v2/videos/{video_id}
    # http://www.adultswim.com/videos/api/v2/videos/{video_id}?fields=stream
    # http://www.adultswim.com/videos/api/v2/videos/{video_id}?fields=id,auth,stream,segments,title,collection_title,season_number,episode_number,description,duration,views,published,images

    _API_URL = 'http://www.adultswim.com/videos/api/v2/videos/'
    _API_FIELDS = 'id,auth,stream,segments,title,collection_title,season_number,episode_number,description,duration,views,published,images'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_path = mobj.group('show_path')
        episode_path = mobj.group('episode_path')

        webpage = self._download_webpage(url, episode_path, 'Downloading page')

        # Adut Swim has loads video information onto pages, the original (and outdated)
        # `bootstrappedData` and the new `__AS_INITIAL_DATA__`. It would seem most
        # pages use `__AS_INITIAL_DATA__` for single videos, however, for playlist
        # `bootstrappedData` is used.

        # Extract the value of `__AS_INITIAL_DATA__` from the Javascript in the page.
        video_page = re.search(r'(?P<var>__AS_INITIAL_DATA__|bootstrappedData) = (?P<json>{.*});', webpage)
        video_var = video_page.group('var')
        video_json = self._parse_json(video_page.group('json'), episode_path)

        if video_var == '__AS_INITIAL_DATA__':
            video_page_info = video_json.get('show', {}).get('sluggedVideo')
            video_id = video_page_info.get('id')
        elif video_var == 'bootstrappedData':
            collections = video_json.get('playlists', {}).get('collections')

            for collection in collections:
                if collection.get('linkURL') == show_path:
                    break

            for video in collection.get('videos'):
                if video.get('slug') == episode_path:
                    break

            # Get steam id, info, & if it needs auth
            if video.get('id'):
                video_id = video.get('id')
        else:
            # Failed to find any variable, new method or no video download option
            raise ExtractorError('Neither __AS_INITIAL_DATA__ or bootstrappedData variables found on page, unable to extract data')

        # Get video information from api via JSON & parse
        video_info = self._download_json('%s%s?fields=%s' % (self._API_URL, video_id, self._API_FIELDS), video_id)

        # Reduce node path
        video_info = video_info.get('data')

        # Inform user if they need to supply authentication
        if video_info.get('auth') is True:
            raise ExtractorError(
                'This video is only available via cable service provider subscription that'
                ' is not currently supported. You may want to use --cookies.', expected=True)

        # Video metadata
        video_title = video_info.get('title')
        video_description = video_info.get('description')
        video_duration = float_or_none(video_info.get('duration'))
        video_series = video_info.get('collection_title')
        video_season_number = int_or_none(video_info.get('season_number'))
        video_episode_number = int_or_none(video_info.get('episode_number'))
        video_episode_title = video_title
        video_timestamp = int_or_none(video_info.get('published'))

        if video_timestamp is not None:
            video_upload_date = datetime.fromtimestamp(video_timestamp).strftime('%Y%m%d')
        else:
            video_upload_date = None

        video_views = int_or_none(video_info.get('views'))

        # Thumbnails
        video_thumbnails = []
        for thumbnail_info in video_info.get('images', []):
            thumbnail_url = thumbnail_info.get('url')
            if not thumbnail_url:
                continue
            video_thumbnails.append({
                'url': thumbnail_url,
                'id': thumbnail_info.get('name'),
                'height': int_or_none(thumbnail_info.get('height')),
                'width': int_or_none(thumbnail_info.get('width')),
            })

        # Extract video and subtitles formats
        # These can be 'streams' for /video/ pages or 'segments' for /playlist/ pages
        assets = []
        if 'stream' in video_info:
            assets.extend(
                video_info.get('stream', {}).get('assets', {})
            )
        elif 'segments' in video_info:
            segments = video_info.get('segments', {})

            for segment in segments:
                assets.extend(
                    segment.get('assets', {})
                )
        else:
            ExtractorError('No video streams or segments found')

        formats = []
        subtitles = {}
        for asset in assets:
            asset_url = asset.get('url')
            asset_ext = determine_ext(asset_url)
            asset_mime = asset.get('mime_type', '')

            if asset_ext == 'm3u8':
                formats.extend(
                    self._extract_m3u8_formats(
                        asset_url,
                        video_id,
                        'mp4',
                        fatal=False
                    )
                )
            elif asset_ext == 'f4m':
                formats.extend(
                    self._extract_f4m_formats(
                        asset_url,
                        video_id,
                        'mp4',
                        fatal=False
                    )
                )
            elif asset_ext == 'flv':
                formats.append({
                    'url': asset_url,
                    'ext': 'flv',
                    'tbr': int_or_none(asset.get('bitrate')),
                    'filesize': int_or_none(asset.get('filesize')),
                })
            elif asset_ext == 'vtt':
                subtitles = self._merge_subtitles(
                    subtitles, {
                        'en': [{
                            'url': asset_url,
                            'ext': 'vtt',
                        }]
                    }
                )
            elif asset_ext == 'scc':
                subtitles = self._merge_subtitles(
                    subtitles, {
                        'en': [{
                            'url': asset_url,
                            'ext': 'scc',
                        }]
                    }
                )
            elif asset_ext == 'xml' and asset_mime == 'application/ttml+xml':
                subtitles = self._merge_subtitles(
                    subtitles, {
                        'en': [{
                            'url': asset_url,
                            'ext': 'ttml',
                        }]
                    }
                )

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': episode_path,
            'formats': formats,
            'title': video_title,
            'description': video_description,
            'duration': video_duration,
            'series': video_series,
            'season_number': video_season_number,
            'episode_number': video_episode_number,
            'episode': video_episode_title,
            'timestamp': video_timestamp,
            'upload_date': video_upload_date,
            'views': video_views,
            'thumbnails': video_thumbnails,
            'subtitles': subtitles,
        }
