# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    qualities,
    strip_or_none,
    try_get,
    update_url_query,
    url_or_none,
)


class VeejoyIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?veejoy.de\/[a-z]{2}\/((?:movies)|(?:series))\/(?P<id>[a-zA-z-/]+)'
    _TESTS = [{
        'url': 'https://www.veejoy.de/en/movies/on-ride-tyrol-log-flume',
        'info_dict': {
            'id': 'on-ride-tyrol-log-flume',
            'ext': 'mp4',
            'title': 'On-ride Tyrol Log Flume',
            'description': 'Through the ‘magical world of diamonds’ and straight into the cool water. Experience a different kind of water slide with the ‘Tyrol Log Flume’. One of the oldest and most popular attractions in the park!',
            'uploader': 'MACK Media',
            'upload_date': '20210923',
            'timestamp': 1632388920
        }
    }, {
        'url': 'https://www.veejoy.de/en/movies/off-to-rulantica',
        'info_dict': {
            'id': 'off-to-rulantica',
            'ext': 'mp4',
            'title': 'Off to Rulantica',
            'description': 'Rocking through the water on round boats, creating splashy fun with water cannons – and then, sliding down ‘Svalgurok’ on ten different slides: Soaking wet water fun is calling.',
            'uploader': 'Veejoy',
            'upload_date': '20220811',
            'timestamp': 1660206600
        }
    }, {
        'url': 'https://www.veejoy.de/de/series/o-the-construction-documentary/the-building-site-grows',
        'info_dict': {
            'id': 'o-the-construction-documentary/the-building-site-grows',
            'ext': 'mp4',
            'title': 'Bau-„Leiter“',
            'description': 'Auf der Baustelle ist viel passiert. Patrick und Lukas bekommen ein Update vom Bauleiter, erklären technische Grundlagen am „lebenden Objekt“ und stellen sich einer Onride-Challenge.',
            'uploader': 'MACK Media',
            'timestamp': 1658997000,
            'upload_date': '20220728'
        }
    }]

    def _search_nextjs_data(self, webpage, video_id, transform_source=None, fatal=True, **kw):
        return self._parse_json(
            self._search_regex(
                r'(?s)<script[^>]+id=[\'"]__NEXT_DATA__[\'"][^>]*>([^<]+)</script>',
                webpage, 'next.js data', fatal=fatal, **kw),
            video_id, transform_source=transform_source, fatal=fatal)

    def get_producer(self, video_data):
        return (
            strip_or_none(
                try_get(video_data, lambda x: x['studioDetails']['item']['title'], compat_str))
            or 'Veejoy')

    def get_thumbnails(self, video_data):
        thumbnails = []

        for res in ('3_4', '16_9'):
            thumb = try_get(video_data, lambda x: x['teaserImage'][res], dict)
            if not thumb:
                continue
            thumb = url_or_none(try_get(thumb, lambda x: x['srcSet'][1].split(' ')[0]))
            if thumb:
                thumbnails.append({
                    'id': res,
                    'url': thumb,
                })

        return thumbnails

    def get_asset_ref(self, video_data):
        for mediaAsset in video_data['mediaAssets']:
            if mediaAsset.get('type') == 'SOURCE':
                return mediaAsset.get('assetReference')

    def get_asset_formats(self, video_data, video_id):
        return self._download_json(
            update_url_query('https://www.veejoy.de/api/service/get-media-summary', {
                'mediaIri': self.get_asset_ref(video_data),
                'locale': 'en'
            }),
            video_id).get('assetFormats')

    def get_original_file_url(self, video_data, video_id):
        for asset_format in self.get_asset_formats(video_data, video_id):
            if asset_format.get('mimeType') == 'video/mp4':
                return asset_format

    def get_video_formats(self, asset_formats, video_id):
        # This function is currently faulty and thus not used
        formats = []

        q = qualities(['hq', 'mq', 'lq'])

        for asset_format in asset_formats:
            f_url = url_or_none(asset_format.get('contentUrl'))
            if not f_url:
                continue
            ext = determine_ext(f_url)
            transcodingFormat = try_get(asset_format, lambda x: x['transcodingFormat'], dict)

            if not transcodingFormat:
                continue

            label = strip_or_none(transcodingFormat.get('label') or '').split('-')
            extra = (
                ('width', int_or_none(transcodingFormat.get('videoWidth'))),
                ('quality', q(label[0])),
                ('language', asset_format.get('language')),
            )
            if ext == 'm3u8':
                # expect 'mimeType': 'application/vnd.apple.mpegurl'
                fmts = self._extract_m3u8_formats(
                    # if the yt-dl HLS downloader doesn't work: `entry_protocol='m3u8'`
                    f_url, video_id, ext='mp4', entry_protocol='m3u8',
                    m3u8_id=transcodingFormat.get('formatType'), fatal=False)
                for f in fmts:
                    f.update((k, v) for k, v in extra if f.get(k) is None)
                formats.extend(fmts)
            else:
                # expect 'mimeType': 'video/mp4'
                fmt = {'url': f_url}
                fmt.update(extra)
                formats.append(fmt)

        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._search_nextjs_data(self._download_webpage(url, video_id), video_id).get('props').get('pageProps').get('media')
        title = video_data.get('title')
        final_url = self.get_original_file_url(video_data, video_id).get('contentUrl')
        producer = self.get_producer(video_data)
        thumbnails = self.get_thumbnails(video_data)

        return {
            'url': final_url,
            'id': video_id,
            'title': title,
            'timestamp': parse_iso8601(video_data.get('liveDate')),
            'description': strip_or_none(video_data.get('shortDescription')),
            'duration': int_or_none(video_data.get('mediaDuration')),
            'uploader': producer,
            'creator': producer,
            'thumbnails': thumbnails,
        }
