# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    float_or_none,
    determine_ext,
    parse_iso8601,
    str_or_none,
    unified_strdate,
    urljoin,
    url_basename,
    remove_end
)


class PuhuTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?puhutv\.com/(?P<id>[a-z0-9-]+)-izle'
    IE_NAME = 'puhutv'
    _TESTS = [
        {
            # A Film
            'url': 'https://puhutv.com/sut-kardesler-izle',
            'md5': 'a347470371d56e1585d1b2c8dab01c96',
            'info_dict': {
                'id': 'sut-kardesler',
                'display_id': '5085',
                'ext': 'mp4',
                'title': 'Süt Kardeşler',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'Arzu Film',
                'description': 'md5:405fd024df916ca16731114eb18e511a',
                'uploader_id': '43',
                'upload_date': '20160729',
                'timestamp': int,
            },
        },
        {
            # An Episode and geo restricted
            'url': 'https://puhutv.com/jet-sosyete-1-bolum-izle',
            'only_matching': True,
        },
        {
            # Has subtitle
            'url': 'https://puhutv.com/dip-1-bolum-izle',
            'only_matching': True,
        }
    ]
    _SUBTITLE_LANGS = {
        'English': 'en',
        'Deutsch': 'de',
        'عربى': 'ar'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            'https://puhutv.com/api/slug/%s-izle' % video_id, video_id)['data']

        display_id = compat_str(info['id'])
        title = info['title']['name']
        if(info.get('display_name') and title is not None):
            title += ' ' + info.get('display_name')

        description = info.get('title', {}).get('description') or info.get('description')
        timestamp = parse_iso8601(info.get('created_at'))
        upload_date = unified_strdate(info.get('created_at'))
        uploader = info.get('title', {}).get('producer', {}).get('name')
        uploader_id = str_or_none(info.get('title', {}).get('producer', {}).get('id'))
        view_count = int_or_none(info.get('content', {}).get('watch_count'))
        duration = float_or_none(info.get('content', {}).get('duration_in_ms'), scale=1000)
        thumbnail = urljoin('https://', info.get('content', {}).get('images', {}).get('wide', {}).get('main'))
        release_year = int_or_none(info.get('title', {}).get('released_at'))
        webpage_url = info.get('web_url')

        # for series
        season_number = int_or_none(info.get('season_number'))
        season_id = int_or_none(info.get('season_id'))
        episode_number = int_or_none(info.get('episode_number'))

        tags = []
        for tag in info.get('title', {}).get('genres', {}):
            if isinstance(tag.get('name'), compat_str):
                tags.append(tag.get('name'))

        thumbnails = []
        thumbs_dict = info.get('content', {}).get('images', {}).get('wide', {})
        if isinstance(thumbs_dict, dict):
            for id, url in thumbs_dict.items():
                if not url or not isinstance(url, compat_str):
                    continue
                url = urljoin('https://', url)
                thumbnails.append({
                    'url': url,
                    'id': id
                })

        subtitles = {}
        for subtitle in info.get('content', {}).get('subtitles', {}):
            if not isinstance(subtitle, dict):
                continue
            lang = subtitle.get('language')
            sub_url = subtitle.get('url')
            if not lang or not isinstance(lang, compat_str) or not sub_url or not isinstance(sub_url, compat_str):
                continue
            subtitles[self._SUBTITLE_LANGS.get(lang, lang)] = [{
                'url': sub_url,
                'ext': determine_ext(sub_url)
            }]

        # Some of videos are geo restricted upon request copyright owner and returns 403
        req_formats = self._download_json(
            'https://puhutv.com/api/assets/%s/videos' % display_id,
            video_id, 'Downloading video JSON', fatal=False)
        if not req_formats:
            self.raise_geo_restricted()

        formats = []
        for format in req_formats['data']['videos']:
            media_url = format.get('url')
            if not media_url or not isinstance(media_url, compat_str):
                continue
            ext = format.get('video_format') or determine_ext(media_url)
            quality = format.get('quality')
            if format.get('stream_type') == 'hls' and format.get('is_playlist') is True:
                m3u8_id = remove_end(url_basename(media_url), '.m3u8')
                formats.append(self._m3u8_meta_format(media_url, ext, m3u8_id=m3u8_id))
            elif ext == 'mp4' and format.get('is_playlist', False) is False:
                formats.append({
                    'url': media_url,
                    'format_id': 'http-%s' % quality,
                    'ext': ext,
                    'height': quality
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'season_id': season_id,
            'season_number': season_number,
            'episode_number': episode_number,
            'release_year': release_year,
            'upload_date': upload_date,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'duration': duration,
            'tags': tags,
            'subtitles': subtitles,
            'webpage_url': webpage_url,
            'thumbnail': thumbnail,
            'thumbnails': thumbnails,
            'formats': formats
        }


class PuhuTVSerieIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?puhutv\.com/(?P<id>[a-z0-9-]+)-detay'
    IE_NAME = 'puhutv:serie'
    _TESTS = [
        {
            'url': 'https://puhutv.com/deniz-yildizi-detay',
            'info_dict': {
                'title': 'Deniz Yıldızı',
                'id': 'deniz-yildizi',
                'uploader': 'Focus Film',
                'uploader_id': 61,
            },
            'playlist_mincount': 234,
        },
        {
            # a film detail page which is using same url with serie page
            'url': 'https://puhutv.com/kaybedenler-kulubu-detay',
            'info_dict': {
                'title': 'Kaybedenler Kulübü',
                'id': 'kaybedenler-kulubu',
                'uploader': 'Tolga Örnek, Murat Dörtbudak, Neslihan Dörtbudak, Kemal Kaplanoğlu',
                'uploader_id': 248,
            },
            'playlist_mincount': 1,
        },
    ]

    def _extract_entries(self, playlist_id, seasons):
        for season in seasons:
            season_id = season['id']
            season_number = season.get('position')
            pagenum = 1
            has_more = True
            while has_more is True:
                query = {
                    'page': pagenum,
                    'per': 40,
                }
                season_info = self._download_json(
                    'https://galadriel.puhutv.com/seasons/%s' % season_id,
                    playlist_id, 'Downloading season %s page %s' % (season_number, pagenum), query=query)
                for episode in season_info.get('episodes'):
                    video_id = episode['slugPath'].replace('-izle', '')
                    yield self.url_result(
                        'https://puhutv.com/%s-izle' % video_id,
                        PuhuTVIE.ie_key(), video_id)
                pagenum = pagenum + 1
                has_more = season_info.get('hasMore', False)

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        info = self._download_json(
            'https://puhutv.com/api/slug/%s-detay' % playlist_id, playlist_id)['data']

        title = info.get('name')
        uploader = info.get('producer', {}).get('name')
        uploader_id = info.get('producer', {}).get('id')
        seasons = info.get('seasons')
        if seasons:
            entries = self._extract_entries(playlist_id, seasons)
        else:
            # For films, these are using same url with series
            video_id = info['assets'][0]['slug']
            return self.url_result(
                'https://puhutv.com/%s-izle' % video_id,
                PuhuTVIE.ie_key(), video_id)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'entries': entries,
        }
