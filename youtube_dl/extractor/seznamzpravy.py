# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urljoin,
    int_or_none,
)


class SeznamZpravyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?seznam\.cz/zpravy/clanek/(?:[-a-z0-9]+)-(?P<id>[0-9]+)'
    _API_URL = 'https://apiclanky.seznam.cz/'
    _MAGIC_SUFFIX = 'spl2,2,VOD'

    _TESTS = [{
        # two videos on one page, with SDN URL
        'url': 'https://www.seznam.cz/zpravy/clanek/jejich-svet-na-nas-utoci-je-lepsi-branit-se-na-jejich-pisecku-rika-reziser-a-major-v-zaloze-marhoul-35990',
        'params': {'skip_download': True},
        # ^ this is here instead of 'file_minsize': 1586, which does not work because
        #   test_download.py forces expected_minsize to at least 10k when test is running
        'info_dict': {
            'id': '35990',
            'ext': 'mp4',
            'title': 'Jejich svět na nás útočí. Je lepší bránit se na jejich písečku, říká režisér a major v záloze Marhoul',
            'description': 'O nasazení českých vojáků v zahraničí. Marhoul by na mise posílal i zálohy. „Nejdříve se ale musí vycvičit,“ říká.',
        }
    }, {
        # video with live stream URL
        'url': 'https://www.seznam.cz/zpravy/clanek/znovu-do-vlady-s-ano-pavel-belobradek-ve-volebnim-specialu-seznamu-38489',
        'info_dict': {
            'id': '38489',
            'ext': 'mp4',
            'title': 'ČSSD a ANO nás s\xa0elektronickou evidencí podrazily, říká šéf lidovců',
            'description': 'Předvolební rozhovory s lídry deseti hlavních stran pokračují. Ve Výzvě Jindřicha Šídla odpovídal předseda lidovců Pavel Bělobrádek.',
        }
    }]

    def _extract_sdn_formats(self, sdn_url, video_id):
        sdn_data = self._download_json(sdn_url, video_id)
        formats = []
        for fmt, fmtdata in sdn_data.get('data', {}).get('mp4', {}).items():
            relative_url = fmtdata.get('url')
            if not relative_url:
                continue

            try:
                width, height = fmtdata.get('resolution')
            except (TypeError, ValueError):
                width, height = None, None

            formats.append({
                'format_id': fmt,
                'width': int_or_none(width),
                'height': int_or_none(height),
                'url': urljoin(sdn_url, relative_url),
            })

        playlists = sdn_data.get('pls', {})
        dash_rel_url = playlists.get('dash', {}).get('url')
        if dash_rel_url:
            formats.extend(self._extract_mpd_formats(urljoin(sdn_url, dash_rel_url), video_id, mpd_id='dash', fatal=False))

        hls_rel_url = playlists.get('hls', {}).get('url')
        if hls_rel_url:
            formats.extend(self._extract_m3u8_formats(urljoin(sdn_url, hls_rel_url), video_id, ext='mp4', m3u8_id='hls', fatal=False))

        self._sort_formats(formats)
        return formats

    def _extract_caption(self, api_data, video_id):
        title = api_data.get('title') or api_data.get('captionTitle')
        caption = api_data.get('caption')
        if not title or not caption:
            return {}

        if 'sdn' in caption.get('video', {}):
            sdn_url = caption['video']['sdn'] + self._MAGIC_SUFFIX
        elif 'liveStreamUrl' in caption:
            sdn_url = self._download_json(caption['liveStreamUrl'] + self._MAGIC_SUFFIX, video_id)['Location']
        else:
            return {}

        formats = self._extract_sdn_formats(sdn_url, video_id)
        if formats:
            return {
                'id': video_id,
                'title': title,
                'description': api_data.get('perex'),
                'display_id': api_data.get('slug'),
                'formats': formats,
            }

    def _extract_content(self, api_data, video_id):
        entries = []
        for num, item in enumerate(api_data.get('content', [])):
            media = item.get('properties', {}).get('media', {})
            sdn_url_part = media.get('video', {}).get('sdn')
            title = media.get('title')
            if not sdn_url_part or not title:
                continue

            entry_id = '%s-%s' % (video_id, num)
            formats = self._extract_sdn_formats(sdn_url_part + self._MAGIC_SUFFIX, entry_id)
            if formats:
                entries.append({
                    'id': entry_id,
                    'title': title,
                    'formats': formats,
                })

        return entries

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_data = self._download_json(self._API_URL + 'v1/documents/' + video_id, video_id)

        caption = self._extract_caption(api_data, video_id)
        content = self._extract_content(api_data, video_id)

        if caption and not content:
            return caption
        else:
            if caption:
                content.insert(0, caption)
            return {
                '_type': 'playlist',
                'entries': content,
                'title': caption.get('title'),
            }
