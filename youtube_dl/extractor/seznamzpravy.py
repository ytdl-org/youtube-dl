# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_str,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    urljoin,
    int_or_none,
    try_get,
    update_url_query,
)


def _raw_id(src_url):
    return compat_urllib_parse_urlparse(src_url).path.split('/')[-1]


class SeznamZpravyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:seznam\.cz/zpravy|seznamzpravy\.cz)/iframe/player\?.*\bsrc='
    _TESTS = [{
        'url': r'https://www.seznamzpravy.cz/iframe/player?duration=241&serviceSlug=zpravy&src=https%3A%2F%2Fv39-a.sdn.szn.cz%2Fv_39%2Fvmd%2F5999c902ea707c67d8e267a9%3Ffl%3Dmdk%2C432f65a0%7C&itemType=video&autoPlay=false&title=Sv%C4%9Bt%20bez%20obalu%3A%20%C4%8Ce%C5%A1t%C3%AD%20voj%C3%A1ci%20na%20mis%C3%ADch%20(kr%C3%A1tk%C3%A1%20verze)&series=Sv%C4%9Bt%20bez%20obalu&serviceName=Seznam%20Zpr%C3%A1vy&poster=%2F%2Fd39-a.sdn.szn.cz%2Fd_39%2Fc_img_F_I%2FR5puJ.jpeg%3Ffl%3Dcro%2C0%2C0%2C1920%2C1080%7Cres%2C1200%2C%2C1%7Cjpg%2C80%2C%2C1&width=1920&height=1080&cutFrom=0&cutTo=0&splVersion=VOD&contentId=170889&contextId=35990&showAdvert=true&collocation=&autoplayPossible=true&embed=&isVideoTooShortForPreroll=false&isVideoTooLongForPostroll=true&videoCommentOpKey=&videoCommentId=&version=4.0.76&dotService=zpravy&gemiusPrismIdentifier=bVc1ZIb_Qax4W2v5xOPGpMeCP31kFfrTzj0SqPTLh_b.Z7&zoneIdPreroll=seznam.pack.videospot&skipOffsetPreroll=5&sectionPrefixPreroll=%2Fzpravy',
        'params': {'skip_download': True},  # 'file_minsize': 1586 seems to get killed in test_download.py
        'info_dict': {
            'id': '170889',
            'ext': 'mp4',
            'title': 'Svět bez obalu: Čeští vojáci na misích (krátká verze)',
        }
    }]

    def _extract_sdn_formats(self, sdn_url, video_id):
        sdn_data = self._download_json(sdn_url, video_id)
        formats = []
        mp4_formats = try_get(sdn_data, lambda x: x['data']['mp4'], dict) or {}
        for fmt, fmtdata in mp4_formats.items():
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
        dash_rel_url = try_get(playlists, lambda x: x['dash']['url'], compat_str)
        if dash_rel_url:
            formats.extend(self._extract_mpd_formats(urljoin(sdn_url, dash_rel_url), video_id, mpd_id='dash', fatal=False))

        hls_rel_url = try_get(playlists, lambda x: x['hls']['url'], compat_str)
        if hls_rel_url:
            formats.extend(self._extract_m3u8_formats(urljoin(sdn_url, hls_rel_url), video_id, ext='mp4', m3u8_id='hls', fatal=False))

        self._sort_formats(formats)
        return formats

    def _real_extract(self, url):
        params = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        src = params['src'][0]
        video_id = params.get('contentId', [_raw_id(src)])[0]

        return {
            'id': video_id,
            'title': params['title'][0],
            'formats': self._extract_sdn_formats(src + 'spl2,2,VOD', video_id),
        }


class SeznamZpravyArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:seznam\.cz/zpravy|seznamzpravy\.cz)/clanek/(?:[-a-z0-9]+)-(?P<id>[0-9]+)'
    _API_URL = 'https://apizpravy.seznam.cz/'

    _TESTS = [{
        # two videos on one page, with SDN URL
        'url': 'https://www.seznamzpravy.cz/clanek/jejich-svet-na-nas-utoci-je-lepsi-branit-se-na-jejich-pisecku-rika-reziser-a-major-v-zaloze-marhoul-35990',
        'params': {'skip_download': True},
        # ^ this is here instead of 'file_minsize': 1586, which does not work because
        #   test_download.py forces expected_minsize to at least 10k when test is running
        'info_dict': {
            'id': '170889',
            'ext': 'mp4',
            'title': 'Svět bez obalu: Čeští vojáci na misích (krátká verze)',
        }
    }, {
        # video with live stream URL
        'url': 'https://www.seznam.cz/zpravy/clanek/znovu-do-vlady-s-ano-pavel-belobradek-ve-volebnim-specialu-seznamu-38489',
        'info_dict': {
            'id': '185688',
            'ext': 'mp4',
            'title': 'Předseda KDU-ČSL Pavel Bělobrádek ve volební Výzvě Seznamu',
        }
    }]

    def _extract_caption(self, api_data, article_id):
        title = api_data.get('title') or api_data.get('captionTitle')
        caption = api_data.get('caption')
        if not title or not caption:
            return {}

        if 'sdn' in caption.get('video', {}):
            src_url = caption['video']['sdn']
        elif 'liveStreamUrl' in caption:
            src_url = self._download_json(caption['liveStreamUrl'], article_id)['Location']
        else:
            return {}

        return {
            'id': caption.get('uid'),
            'title': caption.get('title'),
            'src': src_url,
        }

    def _extract_content(self, api_data):
        entries = []
        for item in api_data.get('content', []):
            media = item.get('properties', {}).get('media', {})
            src_url = media.get('video', {}).get('sdn')
            title = media.get('title')
            if not src_url or not title:
                continue

            entries.append({
                'id': media.get('uid'),
                'title': title,
                'src': src_url,
            })

        return entries

    def _iframe_result(self, info_dict):
        video_id = info_dict['id'] or _raw_id(info_dict['src'])
        url = update_url_query('https://www.seznam.cz/zpravy/iframe/player', {
            'src': info_dict['src'],
            'title': info_dict['title'],
            'contentId': video_id,
            'serviceName': 'Seznam Zprávy',
        })
        return self.url_result(url, ie='SeznamZpravy', video_id=video_id, video_title=info_dict['title'])

    def _real_extract(self, url):
        article_id = self._match_id(url)
        api_data = self._download_json(self._API_URL + 'v1/documents/' + article_id, article_id)

        caption = self._extract_caption(api_data, article_id)
        content = self._extract_content(api_data)

        if caption and not content:
            return self._iframe_result(caption)
        else:
            if caption:
                content.insert(0, caption)
            return self.playlist_result(
                [self._iframe_result(x) for x in content],
                playlist_id=article_id,
                playlist_title=api_data.get('title') or caption.get('title')
            )
