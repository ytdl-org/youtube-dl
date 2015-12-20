# encoding: utf-8
import re

from .common import InfoExtractor


class Tele5IE(InfoExtractor):
    _VALID_URL = r'http://www.tele5.de/(?P<type>re-play/filme|a-z)/(?P<id>.*?).html'

    _TESTS = [{
        'url': 'http://www.tele5.de/re-play/filme/flying-swords-of-dragon-gate.html',
        'info_dict': {
            'ext': 'mp4',
            'id': 'flying-swords-of-dragon-gate',
            'title': 'Flying Swords of Dragon Gate',
        },
    }]

    def _get_video_url(self, thumbnail, entity_id, video_js_url):
        video_js = self._download_webpage(video_js_url, None)
        flavor_id = re.compile(r'''"id\\":\\"(.*?)\\"''').findall(video_js)[-1]
        return thumbnail.split('thumbnail/')[0] + 'playManifest/entryId/{}/flavorId/{}/format/url/protocol/http/a.mp4'.format(entity_id, flavor_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        series = mobj.group('type') == 'a-z'
        webpage = self._download_webpage(url, video_id)

        if series:
            title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title').split('-')[0].strip()
            partner_data =self._html_search_regex(
                r'<script src="(http://api.medianac.com/.*embedIframeJs.*?)"></script>',
                webpage, 'video js').split('/')
            uiconf_id = partner_data[-3]
            partner_id = partner_data[-1]

            entries = []
            for player in re.compile(r'''<div id="kaltura_player_.*?</div>''', re.DOTALL).findall(webpage):
                data = dict(kv for kv in re.compile(r'itemprop="(.*?)" content="(.*?)"').findall(player))
                thumbnail = data['thumbnail']
                entity_id = thumbnail.split('entry_id/')[1].split('/')[0]
                player_id = re.compile(r'id="kaltura_player_(.*?)"').findall(player)[0]
                video_js_url = 'http://api.medianac.com/html5/html5lib/v2.35/mwEmbedFrame.php?&wid=_{partner_id}&uiconf_id={uiconf_id}&cache_st={player_id}&entry_id={entity_id}&flashvars[streamerType]=rtmp&flashvars[mediaProtocol]=rtmp&playerId=kaltura_player_{player_id}&ServiceUrl=http://api.medianac.com&CdnUrl=http://api.medianac.com&ServiceBase=/api_v3/index.php?service=&UseManifestUrls=true&forceMobileHTML5=true&urid=2.35&callback=mwi_kalturaplayer{player_id}'.format(**{
                    'player_id': player_id,
                    'partner_id': partner_id,
                    'uiconf_id': uiconf_id,
                    'entity_id': entity_id,
                })
                video_url = self._get_video_url(thumbnail, entity_id, video_js_url)
                entries.append({
                    'id': entity_id,
                    'title': data['name'],
                    'url': video_url,
                    'thumbnail': data['thumbnail']
                })
            return self.playlist_result(entries, video_id, title)
        else:
            title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title')
            video_js_url =self._html_search_regex(
                    r'<script src="(http://api.medianac.com/.*embedIframeJs.*?)"></script>',
                    webpage, 'video js')
            thumbnail = self._html_search_regex(
                r'<span itemprop="thumbnail" content="(.*?)">',
                webpage, "thumbnail url", fatal=False)
            entity_id = thumbnail.split('entry_id/')[1].split('/')[0]
            video_url = self._get_video_url(thumbnail, entity_id, video_js_url)

            return {
                'ext': 'mp4',
                'id': video_id,
                'thumbnail': thumbnail,
                'title': title,
                'url': video_url,
            }

