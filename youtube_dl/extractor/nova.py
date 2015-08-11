# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    unified_strdate,
)


class NovaIE(InfoExtractor):
    IE_DESC = 'TN.cz, Prásk.tv, Nova.cz, Novaplus.cz, FANDA.tv, Krásná.cz and Doma.cz'
    _VALID_URL = 'http://(?:[^.]+\.)?(?P<site>tv(?:noviny)?|tn|novaplus|vymena|fanda|krasna|doma|prask)\.nova\.cz/(?:[^/]+/)+(?P<id>[^/]+?)(?:\.html|/|$)'
    _TESTS = [{
        'url': 'http://tvnoviny.nova.cz/clanek/novinky/co-na-sebe-sportaci-praskli-vime-jestli-pujde-hrdlicka-na-materskou.html?utm_source=tvnoviny&utm_medium=cpfooter&utm_campaign=novaplus',
        'info_dict': {
            'id': '1608920',
            'display_id': 'co-na-sebe-sportaci-praskli-vime-jestli-pujde-hrdlicka-na-materskou',
            'ext': 'flv',
            'title': 'Duel: Michal Hrdlička a Petr Suchoň',
            'description': 'md5:d0cc509858eee1b1374111c588c6f5d5',
            'thumbnail': 're:^https?://.*\.(?:jpg)',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://tn.nova.cz/clanek/tajemstvi-ukryte-v-podzemi-specialni-nemocnice-v-prazske-krci.html#player_13260',
        'md5': '1dd7b9d5ea27bc361f110cd855a19bd3',
        'info_dict': {
            'id': '1757139',
            'display_id': 'tajemstvi-ukryte-v-podzemi-specialni-nemocnice-v-prazske-krci',
            'ext': 'mp4',
            'title': 'Podzemní nemocnice v pražské Krči',
            'description': 'md5:f0a42dd239c26f61c28f19e62d20ef53',
            'thumbnail': 're:^https?://.*\.(?:jpg)',
        }
    }, {
        'url': 'http://novaplus.nova.cz/porad/policie-modrava/video/5591-policie-modrava-15-dil-blondynka-na-hrbitove',
        'info_dict': {
            'id': '1756825',
            'display_id': '5591-policie-modrava-15-dil-blondynka-na-hrbitove',
            'ext': 'flv',
            'title': 'Policie Modrava - 15. díl - Blondýnka na hřbitově',
            'description': 'md5:dc24e50be5908df83348e50d1431295e',  # Make sure this description is clean of html tags
            'thumbnail': 're:^https?://.*\.(?:jpg)',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://novaplus.nova.cz/porad/televizni-noviny/video/5585-televizni-noviny-30-5-2015/',
        'info_dict': {
            'id': '1756858',
            'ext': 'flv',
            'title': 'Televizní noviny - 30. 5. 2015',
            'thumbnail': 're:^https?://.*\.(?:jpg)',
            'upload_date': '20150530',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'info_dict': {
            'id': '1753621',
            'ext': 'mp4',
            'title': 'Zaklínač 3: Divoký hon',
            'description': 're:.*Pokud se stejně jako my nemůžete.*',
            'thumbnail': 're:https?://.*\.jpg(\?.*)?',
            'upload_date': '20150521',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://sport.tn.nova.cz/clanek/sport/hokej/nhl/zivot-jde-dal-hodnotil-po-vyrazeni-z-playoff-jiri-sekac.html',
        'only_matching': True,
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'only_matching': True,
    }, {
        'url': 'http://doma.nova.cz/clanek/zdravi/prijdte-se-zapsat-do-registru-kostni-drene-jiz-ve-stredu-3-cervna.html',
        'only_matching': True,
    }, {
        'url': 'http://prask.nova.cz/clanek/novinky/co-si-na-sobe-nase-hvezdy-nechaly-pojistit.html',
        'only_matching': True,
    }, {
        'url': 'http://tv.nova.cz/clanek/novinky/zivot-je-zivot-bondovsky-trailer.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        site = mobj.group('site')

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            [r"(?:media|video_id)\s*:\s*'(\d+)'",
             r'media=(\d+)',
             r'id="article_video_(\d+)"',
             r'id="player_(\d+)"'],
            webpage, 'video id')

        config_url = self._search_regex(
            r'src="(http://tn\.nova\.cz/bin/player/videojs/config\.php\?[^"]+)"',
            webpage, 'config url', default=None)

        if not config_url:
            DEFAULT_SITE_ID = '23000'
            SITES = {
                'tvnoviny': DEFAULT_SITE_ID,
                'novaplus': DEFAULT_SITE_ID,
                'vymena': DEFAULT_SITE_ID,
                'krasna': DEFAULT_SITE_ID,
                'fanda': '30',
                'tn': '30',
                'doma': '30',
            }

            site_id = self._search_regex(
                r'site=(\d+)', webpage, 'site id', default=None) or SITES.get(site, DEFAULT_SITE_ID)

            config_url = ('http://tn.nova.cz/bin/player/videojs/config.php?site=%s&media=%s&jsVar=vjsconfig'
                          % (site_id, video_id))

        config = self._download_json(
            config_url, display_id,
            'Downloading config JSON',
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        mediafile = config['mediafile']
        video_url = mediafile['src']

        m = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>[^/]+?))/&*(?P<playpath>.+)$', video_url)
        if m:
            formats = [{
                'url': m.group('url'),
                'app': m.group('app'),
                'play_path': m.group('playpath'),
                'player_path': 'http://tvnoviny.nova.cz/static/shared/app/videojs/video-js.swf',
                'ext': 'flv',
            }]
        else:
            formats = [{
                'url': video_url,
            }]
        self._sort_formats(formats)

        title = mediafile.get('meta', {}).get('title') or self._og_search_title(webpage)
        description = clean_html(self._og_search_description(webpage, default=None))
        thumbnail = config.get('poster')

        if site == 'novaplus':
            upload_date = unified_strdate(self._search_regex(
                r'(\d{1,2}-\d{1,2}-\d{4})$', display_id, 'upload date', default=None))
        elif site == 'fanda':
            upload_date = unified_strdate(self._search_regex(
                r'<span class="date_time">(\d{1,2}\.\d{1,2}\.\d{4})', webpage, 'upload date', default=None))
        else:
            upload_date = None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
        }
