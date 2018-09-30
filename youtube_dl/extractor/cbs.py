from __future__ import unicode_literals

from .common import InfoExtractor
from .theplatform import ThePlatformFeedIE
from ..utils import (
    int_or_none,
    url_or_none,
    js_to_json,
    find_xpath_attr,
    parse_duration,
    xpath_element,
    xpath_text,
    update_url_query,
    urljoin,
)
import datetime


class CBSBaseIE(ThePlatformFeedIE):
    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        closed_caption_e = find_xpath_attr(smil, self._xpath_ns(
            './/param', namespace), 'name', 'ClosedCaptionURL')
        return {
            'en': [{
                'ext': 'ttml',
                'url': closed_caption_e.attrib['value'],
            }]
        } if closed_caption_e is not None and closed_caption_e.attrib.get('value') else []


class CBSPlaylistIE(InfoExtractor):
    IE_DESC = 'CBS series playlists'
    IE_NAME = 'cbs.com:playlist'
    _VALID_URL = r'(?i)https?://(?:www\.)cbs.com/shows/(?P<id>[\w-]+)/?$'
    _TESTS = [
        {
            'url': 'https://www.cbs.com/shows/frasier/',
            'info_dict': {
                'id': 61456196,
                'title': 'Frasier',
            },
            'playlist_count': 264,
        },
        {
            'url': 'https://www.cbs.com/shows/star_trek/',
            'info_dict': {
                'id': 22927,
                'title': 'Star Trek: The Original Series (Remastered)',
            },
            'playlist_count': 79,
        },
    ]

    def extract_episode_info(self, url, json_data):
        episodes = json_data.get('result', {}).get('data')

        entries = []
        for ep in episodes:
            series_title = ep.get('series_title')
            episode_url = url_or_none(urljoin(url, ep.get('url')))
            if episode_url:
                entries.append({
                    '_type': 'url',
                    'id': ep.get('content_id'),
                    'ie_key': 'CBS',
                    'title': ep.get('title'),
                    'url': episode_url,
                    'duration': parse_duration(ep.get('duration')),
                    'thumbnail': ep.get('thumb', {}).get('large'),
                    'upload_date': datetime.datetime.strptime(ep.get('airdate'), '%b %d, %Y').strftime('%Y%m%d'),
                    'episode_title': ep.get('episode_title'),
                    'episode_number': int_or_none(ep.get('episode_number')),
                    'season_number': int_or_none(ep.get('season_number')),
                    'series': ep.get('series_title'),
                })

        return {'series_title': series_title, 'episodes': entries}

    def _real_extract(self, url):
        show_name = self._match_id(url)
        webpage = self._download_webpage(url, show_name)

        show_name_js = self._search_regex(
            r'new CBS\.Show\(([^)]*)\);', webpage, 'show_name')
        show = self._parse_json(show_name_js, show_name,
                                transform_source=js_to_json)
        show_id = show.get('id')

        entries = []
        if show_id:
            offset = 0
            limit = 10
            more_episodes = True
            while (more_episodes):
                episodes_url = urljoin(
                    url, '/carousels/shows/%d/offset/%d/limit/%d/xs/0/' % (show_id, offset, limit))
                json_data = self._download_json(
                    episodes_url, 'Downloading episode playlist')
                result = self.extract_episode_info(url, json_data)
                entries += result['episodes']
                series_title = result['series_title']
                total_episodes = json_data.get('result', {}).get('total')
                offset = offset + limit
                if offset > total_episodes:
                    more_episodes = False

        playlist = self.playlist_result(
            entries, show_id, playlist_title=series_title)
        print(playlist)
        return playlist


class CBSIE(CBSBaseIE):
    _VALID_URL = r'(?:cbs:|https?://(?:www\.)?(?:cbs\.com/shows/[^/]+/video|colbertlateshow\.com/(?:video|podcasts))/)(?P<id>[\w-]+)'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '_u7W953k6la293J7EPTd9oHkSPs6Xn6_',
            'ext': 'mp4',
            'title': 'Connect Chat feat. Garth Brooks',
            'description': 'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            'duration': 1495,
            'timestamp': 1385585425,
            'upload_date': '20131127',
            'uploader': 'CBSI-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'http://colbertlateshow.com/video/8GmB0oY0McANFvp2aEffk9jZZZ2YyXxy/the-colbeard/',
        'only_matching': True,
    }, {
        'url': 'http://www.colbertlateshow.com/podcasts/dYSwjqPs_X1tvbV_P2FcPWRa_qT6akTC/in-the-bad-room-with-stephen/',
        'only_matching': True,
    }]

    def _extract_video_info(self, content_id):
        items_data = self._download_xml(
            'http://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': 'cbs', 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title', True)
        tp_path = 'dJ5BDC/media/guid/2198311517/%s' % content_id
        tp_release_url = 'http://link.theplatform.com/s/' + tp_path

        asset_types = []
        subtitles = {}
        formats = []
        for item in items_data.findall('.//item'):
            asset_type = xpath_text(item, 'assetType')
            if not asset_type or asset_type in asset_types:
                continue
            asset_types.append(asset_type)
            query = {
                'mbr': 'true',
                'assetTypes': asset_type,
            }
            if asset_type.startswith('HLS') or asset_type in ('OnceURL', 'StreamPack'):
                query['formats'] = 'MPEG4,M3U'
            elif asset_type in ('RTMP', 'WIFI', '3G'):
                query['formats'] = 'MPEG4,FLV'
            tp_formats, tp_subtitles = self._extract_theplatform_smil(
                update_url_query(tp_release_url, query), content_id,
                'Downloading %s SMIL data' % asset_type)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        self._sort_formats(formats)

        info = self._extract_theplatform_metadata(tp_path, content_id)
        info.update({
            'id': content_id,
            'title': title,
            'series': xpath_text(video_data, 'seriesTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'duration': int_or_none(xpath_text(video_data, 'videoLength'), 1000),
            'thumbnail': xpath_text(video_data, 'previewImageURL'),
            'formats': formats,
            'subtitles': subtitles,
        })
        return info

    def _real_extract(self, url):
        content_id = self._match_id(url)
        return self._extract_video_info(content_id)
