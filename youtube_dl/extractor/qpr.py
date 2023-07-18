# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    traverse_obj,
    int_or_none,
    url_or_none,
)


class QPRIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?qpr\.co\.uk/videos/(?:highlights|interviews|features)/(?P<id>[0-9a-z-]+)/?'
    _TESTS = [{
        'url': 'https://www.qpr.co.uk/videos/interviews/ainsworth-post-qprpne-070423/',
        'md5': '0a8f4d769719dff161b4096102f20245',
        'info_dict': {
            'id': 'ainsworth-post-qprpne-070423',
            'ext': 'mp4',
            'title': 'Ainsworth on Preston reverse',
            'description': 'QPR head coach Gareth Ainsworth didn’t shy away from the fact that his side are in a relegation battle following Friday’s 2-0 home defeat to Preston North End. Thomas Cannon’s second-half double pushed Rangers further into trouble, with results elsewhere leaving us just a point above the drop zone in the Sky Bet Championship. “I’m gutted for the boys – they’re giving me what they can and it wasn’t good enough today,” Ainsworth told www.qpr.co.uk. “It was the same story again. We conceded some sloppy goals and you can’t afford to do that at this stage of the season when you need wins. “These things are happening at the moment and we need to eradicate them quickly – because we need a win soon. “We’ve also got to be more threatening. We’ve not scored for three games and we don’t look like scoring. “This is a tough league with some good strikers who can open you up. We need to be more threatening.” Ainsworth added: “I’ve not hidden away from the fact that we’re in a relegation battle. When I came here just over a month ago, I knew what I was coming into. “It’s a scrap, it’s a team that’s one once in 18 games. You don’t take over a side like that not expecting some tough days – we’re having too many of them at the moment. “I just want to say thank you to the fans for your support – I’ll always do that. “I took a little bit of abuse at the end, but I did my best and so did the players. We’ll go again on Monday. “You\'re frustrated and I understand. I came here with my eyes wide open, knowing what the case was here. “All I ask is that you continue to get behind us, because negativity can affect the players. I’m hoping that the majority can continue to get behind us and that we can do what’s required.”',
            'thumbnail': r're:^https?://.*\.png.*?$',
            'timestamp': 1680887328,
            'upload_date': '20230407',
            'duration': 289,
            'view_count': 432,
        }
    },
        {
        'url': 'https://www.qpr.co.uk/videos/highlights/highlights-qprpne-080423/',
        'md5': 'f689b8fa93a671805d4cf748064abdba',
        'info_dict': {
            'id': 'highlights-qprpne-080423',
            'ext': 'mp4',
            'title': 'Highlights: QPR 0, Preston North End 2',
            'description': 'WATCH extended highlights from QPR\'s 2-0 defeat against Preston North End at Loftus Road. Thomas Cannon\'s second-half double sunk the R\'s.',
            'thumbnail': r're:^https?://.*\.jpg.*?$',
            'timestamp': 1680943914,
            'upload_date': '20230408',
            'duration': 600,
            'view_count': 26,
        }
    }]

    def _extract_from_player(self, video_src_id, video_id):
        PLAYER_BASE_URL = 'https://open.http.mp.streamamg.com/html5/html5lib/v2.55/mwEmbedFrame.php?&wid=_3000900&uiconf_id=30020502&entry_id='
        MANIFEST_BASE_URL = 'https://open.http.mp.streamamg.com/p/3000900/sp/300090000/playManifest/entryId/'

        player_url = PLAYER_BASE_URL + video_src_id

        player_webpage = self._download_webpage(player_url, video_id, 'Downloading player webpage.')

        raw_video_data = self._search_regex(
            r'window\.kalturaIframePackageData\s*?=\s*?([^;]*)',
            player_webpage,
            'data'
        )

        video_data = self._parse_json(raw_video_data, video_id)
        video_data = video_data['entryResult']

        flavor_assets = video_data['contextData']['flavorAssets']
        flavor_ids = [flavor['id'] for flavor in flavor_assets]
        flavors = ','.join(flavor_ids)

        manifest_url = MANIFEST_BASE_URL + video_src_id + '/flavorIds/' + flavors + '/format/applehttp/protocol/https/a.m3u8'

        formats = self._extract_m3u8_formats(manifest_url, video_id, ext='mp4')
        self._sort_formats(formats)

        return {
            'formats': formats,
            'timestamp': int_or_none(traverse_obj(video_data, ('meta', 'createdAt'))),
            'duration': int_or_none(traverse_obj(video_data, ('meta', 'duration'))),
            'view_count': int_or_none(traverse_obj(video_data, ('meta', 'plays')))
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        raw_description = self._html_search_regex(
            r'<div\s[^>]*class\s*=\s*(?:"|\')\s*article__content row\s*(?:"|\').*?>(.*?)</div>',
            webpage,
            'description_div',
            flags=re.DOTALL
        )
        if raw_description is not None:
            raw_description = raw_description.split('\n')
            raw_description = ' '.join([paragraph.strip() for paragraph in raw_description])

            description = raw_description.replace('\xa0', ' ')
        else:
            description = None

        img_tag = self._search_regex(
            r'(<img[^>]*\sclass\s?=\s?"imageBackgroundCover__img".*?/>)',
            webpage,
            'img',
            flags=re.DOTALL
        )
        raw_thumbnail_urls = self._html_search_regex(
            r'srcset\s?=\s?"([^"]*)"',
            img_tag,
            'thumbnails'
        )

        if raw_thumbnail_urls is not None:
            thumbnail_urls = re.findall(r'https?://\S+', raw_thumbnail_urls)

            thumbnails = []
            for url in thumbnail_urls:
                result = compat_urllib_parse_urlparse(url)
                parameters = compat_urllib_parse_parse_qs(result.query)

                thumbnails.append({
                    'url': url_or_none(url),
                    'preference': int_or_none(traverse_obj(parameters, ('quality', 0))),
                    'width': int_or_none(traverse_obj(parameters, ('width', 0))),
                    'height': int_or_none(traverse_obj(parameters, ('height', 0)))
                })
        else:
            thumbnails = None

        video_src_id = self._search_regex(
            r'<div\s[^>]*\bdata-video-id\s*=\s*"(?P<src_id>[^"]+)"[^>]*>.*?',
            webpage,
            'src_id'
        )
        player_data = self._extract_from_player(video_src_id, video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'formats': player_data['formats'],
            'timestamp': player_data['timestamp'],
            'duration': player_data['duration'],
            'view_count': player_data['view_count'],
        }
