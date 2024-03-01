from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_cookies_SimpleCookie,
    compat_HTTPError,
    compat_str,
    compat_urllib_parse_unquote_plus,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    fix_xml_ampersands,
    int_or_none,
    merge_dicts,
    orderedSet,
    parse_duration,
    qualities,
    str_or_none,
    strip_jsonp,
    unified_strdate,
    unified_timestamp,
    url_or_none,
    urlencode_postdata,
)


class NPOIE(InfoExtractor):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl'
    _VALID_URL = r'''(?x)
                    (?:
                        npo:|
                        https?://
                            (?:www\.)?
                            (?:
                                npo\.nl/(?:[^/]+/)*
                            )
                        )
                        (?P<id>[^/?#]+)
                '''

    _TESTS = [{
        'url': 'https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/',
        # TODO other test attributes
    }, {
        'url': 'http://www.npo.nl/de-mega-mike-mega-thomas-show/27-02-2009/VARA_101191800',
        'md5': 'da50a5787dbfc1603c4ad80f31c5120b',
        'info_dict': {
            'id': 'VARA_101191800',
            'ext': 'm4v',
            'title': 'De Mega Mike & Mega Thomas show: The best of.',
            'description': 'md5:3b74c97fc9d6901d5a665aac0e5400f4',
            'upload_date': '20090227',
            'duration': 2400,
        },
        'skip': 'Video gone',
    }, {
        'url': 'https://npo.nl/start/serie/vpro-tegenlicht/seizoen-11/zwart-geld-de-toekomst-komt-uit-afrika',
        'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
        'info_dict': {
            'id': 'VPWON_1169289',
            'ext': 'm4v',
            'title': 'Tegenlicht: Zwart geld. De toekomst komt uit Afrika',
            'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
            'upload_date': '20130225',
            'duration': 3000,
        },
    }]

    def _get_token(self, video_id):
        return self._download_json(
            'https://npo.nl/start/api/domain/player-token?productId=%s' % video_id,
            video_id,
            note='Downloading token')['token']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._get_info(url, video_id) or self._get_old_info(video_id)

    def _get_info(self, url, video_id):
        _, xsrf_token_response = self._download_webpage_handle(
            'https://www.npostart.nl/api/token', video_id,
            'Downloading token', headers={
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest',
            })
        cookies = compat_cookies_SimpleCookie()
        cookies.load(xsrf_token_response.headers['Set-Cookie'])
        cookies = dict((k, v.value) for k, v in cookies.items())
        xsrf_token = cookies['XSRF-TOKEN']

        player = self._download_json(
            'https://www.npostart.nl/player/%s' % video_id, video_id,
            'Downloading player JSON',
            headers={
                'x-xsrf-token': compat_urllib_parse_unquote_plus(xsrf_token)
            },
            data=urlencode_postdata({
                'autoplay': 0,
                'share': 1,
                'pageUrl': url,
                'isFavourite': 'false',
                'hasAdConsent': 0,
            }))

        player_token = player['token']

        drm = False
        format_urls = set()
        formats = []
        for profile in ('hls', 'dash-widevine', 'dash-playready', 'smooth'):
            streams = self._download_json(
                'https://start-player.npo.nl/video/%s/streams' % video_id,
                video_id, 'Downloading %s profile JSON' % profile, fatal=False,
                query={
                    'profile': profile,
                    'quality': 'npo',
                    'tokenId': player_token,
                    'streamType': 'broadcast',
                },
                # empty data to force a POST request, avoiding HTTP 405
                data=b'')
            if not streams:
                continue
            stream = streams.get('stream')
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('src'))
            if not stream_url or stream_url in format_urls:
                continue
            format_urls.add(stream_url)
            if stream.get('protection') is not None or stream.get('keySystemOptions') is not None:
                drm = True
                continue
            stream_type = stream.get('type')
            stream_ext = determine_ext(stream_url)
            if stream_type == 'application/dash+xml' or stream_ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
            elif stream_type == 'application/vnd.apple.mpegurl' or stream_ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif re.search(r'\.isml?/Manifest', stream_url):
                formats.extend(self._extract_ism_formats(
                    stream_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'url': stream_url,
                })

        if not formats:
            if drm:
                raise ExtractorError('This video is DRM protected.', expected=True)
            return

        self._sort_formats(formats)

        info = {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }

        embed_url = url_or_none(player.get('embedUrl'))
        if embed_url:
            webpage = self._download_webpage(
                embed_url, video_id, 'Downloading embed page', fatal=False)
            if webpage:
                video = self._parse_json(
                    self._search_regex(
                        r'\bvideo\s*=\s*({.+?})\s*;', webpage, 'video',
                        default='{}'), video_id)
                if video:
                    title = video.get('episodeTitle')
                    subtitles = {}
                    subtitles_list = video.get('subtitles')
                    if isinstance(subtitles_list, list):
                        for cc in subtitles_list:
                            cc_url = url_or_none(cc.get('src'))
                            if not cc_url:
                                continue
                            lang = str_or_none(cc.get('language')) or 'nl'
                            subtitles.setdefault(lang, []).append({
                                'url': cc_url,
                            })
                    return merge_dicts({
                        'title': title,
                        'description': video.get('description'),
                        'thumbnail': url_or_none(
                            video.get('still_image_url') or video.get('orig_image_url')),
                        'duration': int_or_none(video.get('duration')),
                        'timestamp': unified_timestamp(video.get('broadcastDate')),
                        'creator': video.get('channel'),
                        'series': video.get('title'),
                        'episode': title,
                        'episode_number': int_or_none(video.get('episodeNumber')),
                        'subtitles': subtitles,
                    }, info)

        return info

    def _get_old_info(self, video_id):
        metadata = self._download_json(
            'http://e.omroep.nl/metadata/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=strip_jsonp,
        )

        error = metadata.get('error')
        if error:
            raise ExtractorError(error, expected=True)

        # For some videos actual video id (prid) is different (e.g. for
        # http://www.omroepwnl.nl/video/fragment/vandaag-de-dag-verkiezingen__POMS_WNL_853698
        # video id is POMS_WNL_853698 but prid is POW_00996502)
        video_id = metadata.get('prid') or video_id

        # titel is too generic in some cases so utilize aflevering_titel as well
        # when available (e.g. http://tegenlicht.vpro.nl/afleveringen/2014-2015/access-to-africa.html)
        title = metadata['titel']
        sub_title = metadata.get('aflevering_titel')
        if sub_title and sub_title != title:
            title += ': %s' % sub_title

        token = self._get_token(video_id)

        formats = []
        urls = set()

        def is_legal_url(format_url):
            return format_url and format_url not in urls and re.match(
                r'^(?:https?:)?//', format_url)

        QUALITY_LABELS = ('Laag', 'Normaal', 'Hoog')
        QUALITY_FORMATS = ('adaptive', 'wmv_sb', 'h264_sb', 'wmv_bb', 'h264_bb', 'wvc1_std', 'h264_std')

        quality_from_label = qualities(QUALITY_LABELS)
        quality_from_format_id = qualities(QUALITY_FORMATS)
        items = self._download_json(
            'http://ida.omroep.nl/app.php/%s' % video_id, video_id,
            'Downloading formats JSON', query={
                'adaptive': 'yes',
                'token': token,
            })['items'][0]
        for num, item in enumerate(items):
            item_url = item.get('url')
            if not is_legal_url(item_url):
                continue
            urls.add(item_url)
            format_id = self._search_regex(
                r'video/ida/([^/]+)', item_url, 'format id',
                default=None)

            item_label = item.get('label')

            def add_format_url(format_url):
                width = int_or_none(self._search_regex(
                    r'(\d+)[xX]\d+', format_url, 'width', default=None))
                height = int_or_none(self._search_regex(
                    r'\d+[xX](\d+)', format_url, 'height', default=None))
                if item_label in QUALITY_LABELS:
                    quality = quality_from_label(item_label)
                    f_id = item_label
                elif item_label in QUALITY_FORMATS:
                    quality = quality_from_format_id(format_id)
                    f_id = format_id
                else:
                    quality, f_id = [None] * 2
                formats.append({
                    'url': format_url,
                    'format_id': f_id,
                    'width': width,
                    'height': height,
                    'quality': quality,
                })

            # Example: http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706
            if item.get('contentType') in ('url', 'audio'):
                add_format_url(item_url)
                continue

            try:
                stream_info = self._download_json(
                    item_url + '&type=json', video_id,
                    'Downloading %s stream JSON'
                    % item_label or item.get('format') or format_id or num)
            except ExtractorError as ee:
                if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 404:
                    error = (self._parse_json(
                        ee.cause.read().decode(), video_id,
                        fatal=False) or {}).get('errorstring')
                    if error:
                        raise ExtractorError(error, expected=True)
                raise
            # Stream URL instead of JSON, example: npo:LI_NL1_4188102
            if isinstance(stream_info, compat_str):
                if not stream_info.startswith('http'):
                    continue
                video_url = stream_info
            # JSON
            else:
                video_url = stream_info.get('url')
            if not video_url or 'vodnotavailable.' in video_url or video_url in urls:
                continue
            urls.add(video_url)
            if determine_ext(video_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            else:
                add_format_url(video_url)

        is_live = metadata.get('medium') == 'live'

        if not is_live:
            for num, stream in enumerate(metadata.get('streams', [])):
                stream_url = stream.get('url')
                if not is_legal_url(stream_url):
                    continue
                urls.add(stream_url)
                # smooth streaming is not supported
                stream_type = stream.get('type', '').lower()
                if stream_type in ['ss', 'ms']:
                    continue
                if stream_type == 'hds':
                    f4m_formats = self._extract_f4m_formats(
                        stream_url, video_id, fatal=False)
                    # f4m downloader downloads only piece of live stream
                    for f4m_format in f4m_formats:
                        f4m_format['preference'] = -1
                    formats.extend(f4m_formats)
                elif stream_type == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        stream_url, video_id, ext='mp4', fatal=False))
                # Example: http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706
                elif '.asf' in stream_url:
                    asx = self._download_xml(
                        stream_url, video_id,
                        'Downloading stream %d ASX playlist' % num,
                        transform_source=fix_xml_ampersands, fatal=False)
                    if not asx:
                        continue
                    ref = asx.find('./ENTRY/Ref')
                    if ref is None:
                        continue
                    video_url = ref.get('href')
                    if not video_url or video_url in urls:
                        continue
                    urls.add(video_url)
                    formats.append({
                        'url': video_url,
                        'ext': stream.get('formaat', 'asf'),
                        'quality': stream.get('kwaliteit'),
                        'preference': -10,
                    })
                else:
                    formats.append({
                        'url': stream_url,
                        'quality': stream.get('kwaliteit'),
                    })

        self._sort_formats(formats)

        subtitles = {}
        if metadata.get('tt888') == 'ja':
            subtitles['nl'] = [{
                'ext': 'vtt',
                'url': 'http://tt888.omroep.nl/tt888/%s' % video_id,
            }]

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': metadata.get('info'),
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'upload_date': unified_strdate(metadata.get('gidsdatum')),
            'duration': parse_duration(metadata.get('tijdsduur')),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }

###############################################################
#   Description of the new process of getting to the stream   #
###############################################################

# Valid URLs for new tests
# https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/
# https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/afspelen

# Step 1: Normalize the URL
# If the URL ends with /afspelen, strip that
# We need the slug in the next stepto find the productId

# Step 2: Find the productId
# In the contents of the URL is a JSON blob:
# <script id="__NEXT_DATA__" type="application/json">
# There's a list of queries in the ['props']['pageProps']['dehydratedState']['queries'] key
# In this list of queries, one is the current episode
# This one can be found by looping over queries and selecting
# the one where the key ['state']['data']['slug'] contains the last part of the URL
# In the test case 'wie-is-de-mol-2'
# We need the productId from the corresponding entry in ['state']['data']['productId']
# This looks a bit GraphQL-like, so there might be an easier way to query the productId, if we know the slug

# Step 3: Get the JWT
# With this productId we can get a player-token
# https://npo.nl/start/api/domain/player-token?productId=VARA_101372912
# The response is a JSON dictionary, with one key ['token']
# In this key is a JWT

# Step 4: Get the stream-link json
# The JWT needs to be put in the Authorization header in a POST request to
# https://prod.npoplayer.nl/stream-link
# with the following payload (for this test case)
# {
#   "profileName": "dash",
#   "drmType": "widevine",
#   "referrerUrl": "https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/afspelen"
# }
# Even though the request asks for Widevine DRM, it's not always available
# At this point we don't know whether there's DRM yet

# Step 5: Get the stream.mpd from the JSON response and find out if DRM is enabled
# This returns a JSON response with a stream.mpd file in the ['stream']['streamURL'] key
# If dash_unencrypted is in this URL it's a stream without DRM and we can download it

# For all new content there most likely is DRM protection on the stream
# In that case dash_cenc is in the stream.mpd URL


##############################################################
#   Differences when embedded on the broadcaster's website   #
##############################################################

# The same episode is also embedded on the broadcaster's website: https://bnnvara.nl/videos/27455
# It's nice to support that too, and in the case of bnnvara.nl (and maybe more broadcasters)
# it's even easier to get to the productId
# By POSTing to the GraphQL endpoint at we can query using the id (last part of the URL)
# https://api.bnnvara.nl/bff/graphql
# {
#   "operationName": "getMedia",
#   "variables": {
#     "id": "27455",
#     "hasAdConsent": false,
#     "atInternetId": 70
#   },
#   "query": "query getMedia($id: ID!, $mediaUrl: String, $hasAdConsent: Boolean!, $atInternetId: Int) {\n  player(\n    id: $id\n    mediaUrl: $mediaUrl\n    hasAdConsent: $hasAdConsent\n    atInternetId: $atInternetId\n  ) {\n    ... on PlayerSucces {\n      brand {\n        name\n        slug\n        broadcastsEnabled\n        __typename\n      }\n      title\n      programTitle\n      pomsProductId\n      broadcasters {\n        name\n        __typename\n      }\n      duration\n      classifications {\n        title\n        imageUrl\n        type\n        __typename\n      }\n      image {\n        title\n        url\n        __typename\n      }\n      cta {\n        title\n        url\n        __typename\n      }\n      genres {\n        name\n        __typename\n      }\n      subtitles {\n        url\n        language\n        __typename\n      }\n      sources {\n        name\n        url\n        ratio\n        __typename\n      }\n      type\n      token\n      __typename\n    }\n    ... on PlayerError {\n      error\n      __typename\n    }\n    __typename\n  }\n}"
# }
# The response is in the key ['data']['player']['pomsProductId']
# From this point it's possible to continue at step 3 of the description above
