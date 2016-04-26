from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import strip_jsonp


class Tele5IE(InfoExtractor):
    _VALID_URL = r'http://www\.tele5\.de/a-z/(?P<id>.+)\.html'

    _TEST = {
        'url': 'http://www.tele5.de/a-z/man-vs-fly/ganze-folgen/video/boxer.html',
        'md5': '620973dde66000285b6a17d04d3950b8',
        'info_dict': {
            'id': '0_3vnqiwvl',
            'ext': 'mp4',
            'title': 'Man vs. Fly - Boxer (1)',
            'duration': 296,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_script = self._search_regex(r'(?s)<script>\s*kWidget\.thumbEmbed\((\{.+?\})\);\s*</script>',
            webpage, 'player script')
        video_params = self._parse_json(video_script, 'player script')
        video_js_url = ('http://api.medianac.com/html5/html5lib/v2.39/mwEmbedFrame.php?'
            '&wid={wid}'
            '&uiconf_id={uiconf_id}'
            '&cache_st={cache_st}'
            '&entry_id={entry_id}'
            '&flashvars[streamerType]=rtmp'
            '&flashvars[mediaProtocol]=rtmp'
            '&playerId={targetId}'
            '&ServiceUrl=http%3A%2F%2Fapi.medianac.com'
            '&CdnUrl=http%3A%2F%2Fapi.medianac.com'
            '&ServiceBase=%2Fapi_v3%2Findex.php%3Fservice%3D'
            '&UseManifestUrls=true'
            '&forceMobileHTML5=true'
            '&urid=2.39'
            '&callback=mwi_kalturaplayer{cache_st}').format(**video_params)

        html = self._download_json(video_js_url, 'video js', transform_source=strip_jsonp)['content']
        info = self._search_regex(r'window\.kalturaIframePackageData = (\{.*?\}\});', html, None)
        info = self._parse_json(info, None)['entryResult']

        base = info['meta']['thumbnailUrl'].partition('/thumbnail/')[0]
        url_tmpl = base + '/playManifest/entryId/{entryId}/flavorId/{id}/format/url/protocol/http/a.mp4'
        return {
            'id': info['meta']['id'],
            'title': info['meta']['name'],
            'duration': info['meta']['duration'],
            'formats': [{
                'url': url_tmpl.format(**f),
                'ext': f['fileExt'],
                'format_id': str(f['flavorParamsId']),
                'width': f['width'],
                'height': f['height'],
                'tbr': f['bitrate'],
                'fps': f['frameRate'],
                'filesize': f['size']
            } for f in info['contextData']['flavorAssets']]
        }
