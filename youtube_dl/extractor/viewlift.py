from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    js_to_json,
    parse_age_limit,
    parse_duration,
    try_get,
)


class ViewLiftBaseIE(InfoExtractor):
    _DOMAINS_REGEX = r'(?:(?:main\.)?snagfilms|snagxtreme|funnyforfree|kiddovid|winnersview|(?:monumental|lax)sportsnetwork|vayafilm)\.com|hoichoi\.tv'


class ViewLiftEmbedIE(ViewLiftBaseIE):
    _VALID_URL = r'https?://(?:(?:www|embed)\.)?(?:%s)/embed/player\?.*\bfilmId=(?P<id>[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12})' % ViewLiftBaseIE._DOMAINS_REGEX
    _TESTS = [{
        'url': 'http://embed.snagfilms.com/embed/player?filmId=74849a00-85a9-11e1-9660-123139220831&w=500',
        'md5': '2924e9215c6eff7a55ed35b72276bd93',
        'info_dict': {
            'id': '74849a00-85a9-11e1-9660-123139220831',
            'ext': 'mp4',
            'title': '#whilewewatch',
        }
    }, {
        # invalid labels, 360p is better that 480p
        'url': 'http://www.snagfilms.com/embed/player?filmId=17ca0950-a74a-11e0-a92a-0026bb61d036',
        'md5': '882fca19b9eb27ef865efeeaed376a48',
        'info_dict': {
            'id': '17ca0950-a74a-11e0-a92a-0026bb61d036',
            'ext': 'mp4',
            'title': 'Life in Limbo',
        }
    }, {
        'url': 'http://www.snagfilms.com/embed/player?filmId=0000014c-de2f-d5d6-abcf-ffef58af0017',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:embed\.)?(?:%s)/embed/player.+?)\1' % ViewLiftBaseIE._DOMAINS_REGEX,
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if '>This film is not playable in your area.<' in webpage:
            raise ExtractorError(
                'Film %s is not playable in your area.' % video_id, expected=True)

        formats = []
        has_bitrate = False
        sources = self._parse_json(self._search_regex(
            r'(?s)sources:\s*(\[.+?\]),', webpage,
            'sources', default='[]'), video_id, js_to_json)
        for source in sources:
            file_ = source.get('file')
            if not file_:
                continue
            type_ = source.get('type')
            ext = determine_ext(file_)
            format_id = source.get('label') or ext
            if all(v in ('m3u8', 'hls') for v in (type_, ext)):
                formats.extend(self._extract_m3u8_formats(
                    file_, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                bitrate = int_or_none(self._search_regex(
                    [r'(\d+)kbps', r'_\d{1,2}x\d{1,2}_(\d{3,})\.%s' % ext],
                    file_, 'bitrate', default=None))
                if not has_bitrate and bitrate:
                    has_bitrate = True
                height = int_or_none(self._search_regex(
                    r'^(\d+)[pP]$', format_id, 'height', default=None))
                formats.append({
                    'url': file_,
                    'format_id': 'http-%s%s' % (format_id, ('-%dk' % bitrate if bitrate else '')),
                    'tbr': bitrate,
                    'height': height,
                })
        if not formats:
            hls_url = self._parse_json(self._search_regex(
                r'filmInfo\.src\s*=\s*({.+?});',
                webpage, 'src'), video_id, js_to_json)['src']
            formats = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
        field_preference = None if has_bitrate else ('height', 'tbr', 'format_id')
        self._sort_formats(formats, field_preference)

        title = self._search_regex(
            [r"title\s*:\s*'([^']+)'", r'<title>([^<]+)</title>'],
            webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class ViewLiftIE(ViewLiftBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>%s)(?:/(?:films/title|show|(?:news/)?videos?))?/(?P<id>[^?#]+)' % ViewLiftBaseIE._DOMAINS_REGEX
    _TESTS = [{
        'url': 'http://www.snagfilms.com/films/title/lost_for_life',
        'md5': '19844f897b35af219773fd63bdec2942',
        'info_dict': {
            'id': '0000014c-de2f-d5d6-abcf-ffef58af0017',
            'display_id': 'lost_for_life',
            'ext': 'mp4',
            'title': 'Lost for Life',
            'description': 'md5:ea10b5a50405ae1f7b5269a6ec594102',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 4489,
            'categories': 'mincount:3',
            'age_limit': 14,
            'upload_date': '20150421',
            'timestamp': 1429656820,
        }
    }, {
        'url': 'http://www.snagfilms.com/show/the_world_cut_project/india',
        'md5': 'e6292e5b837642bbda82d7f8bf3fbdfd',
        'info_dict': {
            'id': '00000145-d75c-d96e-a9c7-ff5c67b20000',
            'display_id': 'the_world_cut_project/india',
            'ext': 'mp4',
            'title': 'India',
            'description': 'md5:5c168c5a8f4719c146aad2e0dfac6f5f',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 979,
            'timestamp': 1399478279,
            'upload_date': '20140507',
        }
    }, {
        'url': 'http://main.snagfilms.com/augie_alone/s_2_ep_12_love',
        'info_dict': {
            'id': '00000148-7b53-de26-a9fb-fbf306f70020',
            'display_id': 'augie_alone/s_2_ep_12_love',
            'ext': 'mp4',
            'title': 'Augie, Alone:S. 2 Ep. 12 - Love',
            'description': 'md5:db2a5c72d994f16a780c1eb353a8f403',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 107,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://main.snagfilms.com/films/title/the_freebie',
        'only_matching': True,
    }, {
        # Film is not playable in your area.
        'url': 'http://www.snagfilms.com/films/title/inside_mecca',
        'only_matching': True,
    }, {
        # Film is not available.
        'url': 'http://www.snagfilms.com/show/augie_alone/flirting',
        'only_matching': True,
    }, {
        'url': 'http://www.winnersview.com/videos/the-good-son',
        'only_matching': True,
    }, {
        # Was once Kaltura embed
        'url': 'https://www.monumentalsportsnetwork.com/videos/john-carlson-postgame-2-25-15',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        domain, display_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, display_id)

        if ">Sorry, the Film you're looking for is not available.<" in webpage:
            raise ExtractorError(
                'Film %s is not available.' % display_id, expected=True)

        initial_store_state = self._search_regex(
            r"window\.initialStoreState\s*=.*?JSON\.parse\(unescape\(atob\('([^']+)'\)\)\)",
            webpage, 'Initial Store State', default=None)
        if initial_store_state:
            modules = self._parse_json(compat_urllib_parse_unquote(base64.b64decode(
                initial_store_state).decode()), display_id)['page']['data']['modules']
            content_data = next(m['contentData'][0] for m in modules if m.get('moduleType') == 'VideoDetailModule')
            gist = content_data['gist']
            film_id = gist['id']
            title = gist['title']
            video_assets = try_get(
                content_data, lambda x: x['streamingInfo']['videoAssets'], dict)
            if not video_assets:
                token = self._download_json(
                    'https://prod-api.viewlift.com/identity/anonymous-token',
                    film_id, 'Downloading authorization token',
                    query={'site': 'snagfilms'})['authorizationToken']
                video_assets = self._download_json(
                    'https://prod-api.viewlift.com/entitlement/video/status',
                    film_id, headers={
                        'Authorization': token,
                        'Referer': url,
                    }, query={
                        'id': film_id
                    })['video']['streamingInfo']['videoAssets']

            formats = []
            mpeg_video_assets = video_assets.get('mpeg') or []
            for video_asset in mpeg_video_assets:
                video_asset_url = video_asset.get('url')
                if not video_asset:
                    continue
                bitrate = int_or_none(video_asset.get('bitrate'))
                height = int_or_none(self._search_regex(
                    r'^_?(\d+)[pP]$', video_asset.get('renditionValue'),
                    'height', default=None))
                formats.append({
                    'url': video_asset_url,
                    'format_id': 'http%s' % ('-%d' % bitrate if bitrate else ''),
                    'tbr': bitrate,
                    'height': height,
                    'vcodec': video_asset.get('codec'),
                })

            hls_url = video_assets.get('hls')
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, film_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
            self._sort_formats(formats, ('height', 'tbr', 'format_id'))

            info = {
                'id': film_id,
                'display_id': display_id,
                'title': title,
                'description': gist.get('description'),
                'thumbnail': gist.get('videoImageUrl'),
                'duration': int_or_none(gist.get('runtime')),
                'age_limit': parse_age_limit(content_data.get('parentalRating')),
                'timestamp': int_or_none(gist.get('publishDate'), 1000),
                'formats': formats,
            }
            for k in ('categories', 'tags'):
                info[k] = [v['title'] for v in content_data.get(k, []) if v.get('title')]
            return info
        else:
            film_id = self._search_regex(r'filmId=([\da-f-]{36})"', webpage, 'film id')

            snag = self._parse_json(
                self._search_regex(
                    r'Snag\.page\.data\s*=\s*(\[.+?\]);', webpage, 'snag', default='[]'),
                display_id)

            for item in snag:
                if item.get('data', {}).get('film', {}).get('id') == film_id:
                    data = item['data']['film']
                    title = data['title']
                    description = clean_html(data.get('synopsis'))
                    thumbnail = data.get('image')
                    duration = int_or_none(data.get('duration') or data.get('runtime'))
                    categories = [
                        category['title'] for category in data.get('categories', [])
                        if category.get('title')]
                    break
            else:
                title = self._html_search_regex(
                    (r'itemprop="title">([^<]+)<',
                     r'(?s)itemprop="title">(.+?)<div'), webpage, 'title')
                description = self._html_search_regex(
                    r'(?s)<div itemprop="description" class="film-synopsis-inner ">(.+?)</div>',
                    webpage, 'description', default=None) or self._og_search_description(webpage)
                thumbnail = self._og_search_thumbnail(webpage)
                duration = parse_duration(self._search_regex(
                    r'<span itemprop="duration" class="film-duration strong">([^<]+)<',
                    webpage, 'duration', fatal=False))
                categories = re.findall(r'<a href="/movies/[^"]+">([^<]+)</a>', webpage)

            return {
                '_type': 'url_transparent',
                'url': 'http://%s/embed/player?filmId=%s' % (domain, film_id),
                'id': film_id,
                'display_id': display_id,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'duration': duration,
                'categories': categories,
                'ie_key': 'ViewLiftEmbed',
            }
