# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .jwplatform import JWPlatformBaseIE
from ..compat import compat_str


class RENTVIE(JWPlatformBaseIE):
    _VALID_URL = r'(?:rentv:|https?://(?:www\.)?ren\.tv/(?:player|video/epizod)/)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://ren.tv/video/epizod/118577',
        'md5': 'd91851bf9af73c0ad9b2cdf76c127fbb',
        'info_dict': {
            'id': '118577',
            'ext': 'mp4',
            'title': 'Документальный спецпроект: "Промывка мозгов. Технологии XXI века"'
        }
    }, {
        'url': 'http://ren.tv/player/118577',
        'only_matching': True,
    }, {
        'url': 'rentv:118577',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://ren.tv/player/' + video_id, video_id)
        jw_config = self._parse_json(self._search_regex(
            r'config\s*=\s*({.+});', webpage, 'jw config'), video_id)
        return self._parse_jwplayer_data(jw_config, video_id, m3u8_id='hls')


class RENTVArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ren\.tv/novosti/\d{4}-\d{2}-\d{2}/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://ren.tv/novosti/2016-10-26/video-mikroavtobus-popavshiy-v-dtp-s-gruzovikami-v-podmoskove-prevratilsya-v',
        'md5': 'ebd63c4680b167693745ab91343df1d6',
        'info_dict': {
            'id': '136472',
            'ext': 'mp4',
            'title': 'Видео: микроавтобус, попавший в ДТП с грузовиками в Подмосковье, превратился в груду металла',
            'description': 'Жертвами столкновения двух фур и микроавтобуса, по последним данным, стали семь человек.',
        }
    }, {
        # TODO: invalid m3u8
        'url': 'http://ren.tv/novosti/2015-09-25/sluchaynyy-prohozhiy-poymal-avtougonshchika-v-murmanske-video',
        'info_dict': {
            'id': 'playlist',
            'ext': 'mp4',
            'title': 'Случайный прохожий поймал автоугонщика в Мурманске. ВИДЕО | РЕН ТВ',
            'uploader': 'ren.tv',
        },
        'params': {
            # m3u8 downloads
            'skip_download': True,
        },
        'skip': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        drupal_settings = self._parse_json(self._search_regex(
            r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
            webpage, 'drupal settings'), display_id)

        entries = []
        for config_profile in drupal_settings.get('ren_jwplayer', {}).values():
            media_id = config_profile.get('mediaid')
            if not media_id:
                continue
            media_id = compat_str(media_id)
            entries.append(self.url_result('rentv:' + media_id, 'RENTV', media_id))
        return self.playlist_result(entries, display_id)
