# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    js_to_json,
    smuggle_url,
    try_get,
    xpath_text,
    xpath_element,
    xpath_with_ns,
    find_xpath_attr,
    parse_iso8601,
    parse_age_limit,
    int_or_none,
    ExtractorError,
)


class CBCIE(InfoExtractor):
    IE_NAME = 'cbc.ca'
    _VALID_URL = r'https?://(?:www\.)?cbc\.ca/(?!player/)(?:[^/]+/)+(?P<id>[^/?#]+)'
    _TESTS = [{
        # with mediaId
        'url': 'http://www.cbc.ca/22minutes/videos/clips-season-23/don-cherry-play-offs',
        'md5': '97e24d09672fc4cf56256d6faa6c25bc',
        'info_dict': {
            'id': '2682904050',
            'ext': 'mp4',
            'title': 'Don Cherry – All-Stars',
            'description': 'Don Cherry has a bee in his bonnet about AHL player John Scott because that guy’s got heart.',
            'timestamp': 1454463000,
            'upload_date': '20160203',
            'uploader': 'CBCC-NEW',
        },
        'skip': 'Geo-restricted to Canada',
    }, {
        # with clipId, feed available via tpfeed.cbc.ca and feed.theplatform.com
        'url': 'http://www.cbc.ca/22minutes/videos/22-minutes-update/22-minutes-update-episode-4',
        'md5': '162adfa070274b144f4fdc3c3b8207db',
        'info_dict': {
            'id': '2414435309',
            'ext': 'mp4',
            'title': '22 Minutes Update: What Not To Wear Quebec',
            'description': "This week's latest Canadian top political story is What Not To Wear Quebec.",
            'upload_date': '20131025',
            'uploader': 'CBCC-NEW',
            'timestamp': 1382717907,
        },
    }, {
        # with clipId, feed only available via tpfeed.cbc.ca
        'url': 'http://www.cbc.ca/archives/entry/1978-robin-williams-freestyles-on-90-minutes-live',
        'md5': '0274a90b51a9b4971fe005c63f592f12',
        'info_dict': {
            'id': '2487345465',
            'ext': 'mp4',
            'title': 'Robin Williams freestyles on 90 Minutes Live',
            'description': 'Wacky American comedian Robin Williams shows off his infamous "freestyle" comedic talents while being interviewed on CBC\'s 90 Minutes Live.',
            'upload_date': '19780210',
            'uploader': 'CBCC-NEW',
            'timestamp': 255977160,
        },
    }, {
        # multiple iframes
        'url': 'http://www.cbc.ca/natureofthings/blog/birds-eye-view-from-vancouvers-burrard-street-bridge-how-we-got-the-shot',
        'playlist': [{
            'md5': '377572d0b49c4ce0c9ad77470e0b96b4',
            'info_dict': {
                'id': '2680832926',
                'ext': 'mp4',
                'title': 'An Eagle\'s-Eye View Off Burrard Bridge',
                'description': 'Hercules the eagle flies from Vancouver\'s Burrard Bridge down to a nearby park with a mini-camera strapped to his back.',
                'upload_date': '20160201',
                'timestamp': 1454342820,
                'uploader': 'CBCC-NEW',
            },
        }, {
            'md5': '415a0e3f586113894174dfb31aa5bb1a',
            'info_dict': {
                'id': '2658915080',
                'ext': 'mp4',
                'title': 'Fly like an eagle!',
                'description': 'Eagle equipped with a mini camera flies from the world\'s tallest tower',
                'upload_date': '20150315',
                'timestamp': 1426443984,
                'uploader': 'CBCC-NEW',
            },
        }],
        'skip': 'Geo-restricted to Canada',
    }]

    @classmethod
    def suitable(cls, url):
        return False if CBCPlayerIE.suitable(url) else super(CBCIE, cls).suitable(url)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        player_init = self._search_regex(
            r'CBC\.APP\.Caffeine\.initInstance\(({.+?})\);', webpage, 'player init',
            default=None)
        if player_init:
            player_info = self._parse_json(player_init, display_id, js_to_json)
            media_id = player_info.get('mediaId')
            if not media_id:
                clip_id = player_info['clipId']
                feed = self._download_json(
                    'http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?byCustomValue={:mpsReleases}{%s}' % clip_id,
                    clip_id, fatal=False)
                if feed:
                    media_id = try_get(feed, lambda x: x['entries'][0]['guid'], compat_str)
                if not media_id:
                    media_id = self._download_json(
                        'http://feed.theplatform.com/f/h9dtGB/punlNGjMlc1F?fields=id&byContent=byReleases%3DbyId%253D' + clip_id,
                        clip_id)['entries'][0]['id'].split('/')[-1]
            return self.url_result('cbcplayer:%s' % media_id, 'CBCPlayer', media_id)
        else:
            entries = [self.url_result('cbcplayer:%s' % media_id, 'CBCPlayer', media_id) for media_id in re.findall(r'<iframe[^>]+src="[^"]+?mediaId=(\d+)"', webpage)]
            return self.playlist_result(entries)


class CBCPlayerIE(InfoExtractor):
    IE_NAME = 'cbc.ca:player'
    _VALID_URL = r'(?:cbcplayer:|https?://(?:www\.)?cbc\.ca/(?:player/play/|i/caffeine/syndicate/\?mediaId=))(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.cbc.ca/player/play/2683190193',
        'md5': '64d25f841ddf4ddb28a235338af32e2c',
        'info_dict': {
            'id': '2683190193',
            'ext': 'mp4',
            'title': 'Gerry Runs a Sweat Shop',
            'description': 'md5:b457e1c01e8ff408d9d801c1c2cd29b0',
            'timestamp': 1455071400,
            'upload_date': '20160210',
            'uploader': 'CBCC-NEW',
        },
        'skip': 'Geo-restricted to Canada',
    }, {
        # Redirected from http://www.cbc.ca/player/AudioMobile/All%20in%20a%20Weekend%20Montreal/ID/2657632011/
        'url': 'http://www.cbc.ca/player/play/2657631896',
        'md5': 'e5e708c34ae6fca156aafe17c43e8b75',
        'info_dict': {
            'id': '2657631896',
            'ext': 'mp3',
            'title': 'CBC Montreal is organizing its first ever community hackathon!',
            'description': 'The modern technology we tend to depend on so heavily, is never without it\'s share of hiccups and headaches. Next weekend - CBC Montreal will be getting members of the public for its first Hackathon.',
            'timestamp': 1425704400,
            'upload_date': '20150307',
            'uploader': 'CBCC-NEW',
        },
    }, {
        # available only when we add `formats=MPEG4,FLV,MP3` to theplatform url
        'url': 'http://www.cbc.ca/player/play/2164402062',
        'md5': '17a61eb813539abea40618d6323a7f82',
        'info_dict': {
            'id': '2164402062',
            'ext': 'flv',
            'title': 'Cancer survivor four times over',
            'description': 'Tim Mayer has beaten three different forms of cancer four times in five years.',
            'timestamp': 1320410746,
            'upload_date': '20111104',
            'uploader': 'CBCC-NEW',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/ExhSPC/media/guid/2655402169/%s?mbr=true&formats=MPEG4,FLV,MP3' % video_id, {
                    'force_smil_url': True
                }),
            'id': video_id,
        }


class CBCWatchBaseIE(InfoExtractor):
    _device_id = None
    _device_token = None
    _API_BASE_URL = 'https://api-cbc.cloud.clearleap.com/cloffice/client/'
    _NS_MAP = {
        'media': 'http://search.yahoo.com/mrss/',
        'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/',
    }

    def _call_api(self, path, video_id):
        url = path if path.startswith('http') else self._API_BASE_URL + path
        result = self._download_xml(url, video_id, headers={
            'X-Clearleap-DeviceId': self._device_id,
            'X-Clearleap-DeviceToken': self._device_token,
        })
        error_message = xpath_text(result, 'userMessage') or xpath_text(result, 'systemMessage')
        if error_message:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error_message))
        return result

    def _real_initialize(self):
        if not self._device_id or not self._device_token:
            device = self._downloader.cache.load('cbcwatch', 'device') or {}
            self._device_id, self._device_token = device.get('id'), device.get('token')
            if not self._device_id or not self._device_token:
                result = self._download_xml(
                    self._API_BASE_URL + 'device/register',
                    None, data=b'<device><type>web</type></device>')
                self._device_id = xpath_text(result, 'deviceId', fatal=True)
                self._device_token = xpath_text(result, 'deviceToken', fatal=True)
                self._downloader.cache.store(
                    'cbcwatch', 'device', {
                        'id': self._device_id,
                        'token': self._device_token,
                    })

    def _parse_rss_feed(self, rss):
        channel = xpath_element(rss, 'channel', fatal=True)

        def _add_ns(path):
            return xpath_with_ns(path, self._NS_MAP)

        entries = []
        for item in channel.findall('item'):
            guid = xpath_text(item, 'guid', fatal=True)
            title = xpath_text(item, 'title', fatal=True)

            media_group = xpath_element(item, _add_ns('media:group'), fatal=True)
            content = xpath_element(media_group, _add_ns('media:content'), fatal=True)
            content_url = content.attrib['url']

            thumbnails = []
            for thumbnail in media_group.findall(_add_ns('media:thumbnail')):
                thumbnail_url = thumbnail.get('url')
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'id': thumbnail.get('profile'),
                    'url': thumbnail_url,
                    'width': int_or_none(thumbnail.get('width')),
                    'height': int_or_none(thumbnail.get('height')),
                })

            timestamp = None
            release_date = find_xpath_attr(
                item, _add_ns('media:credit'), 'role', 'releaseDate')
            if release_date is not None:
                timestamp = parse_iso8601(release_date.text)

            entries.append({
                '_type': 'url_transparent',
                'url': content_url,
                'id': guid,
                'title': title,
                'description': xpath_text(item, 'description'),
                'timestamp': timestamp,
                'duration': int_or_none(content.get('duration')),
                'age_limit': parse_age_limit(xpath_text(item, _add_ns('media:rating'))),
                'episode': xpath_text(item, _add_ns('clearleap:episode')),
                'episode_number': int_or_none(xpath_text(item, _add_ns('clearleap:episodeInSeason'))),
                'series': xpath_text(item, _add_ns('clearleap:series')),
                'season_number': int_or_none(xpath_text(item, _add_ns('clearleap:season'))),
                'thumbnails': thumbnails,
                'ie_key': 'CBCWatchVideo',
            })

        return self.playlist_result(
            entries, xpath_text(channel, 'guid'),
            xpath_text(channel, 'title'),
            xpath_text(channel, 'description'))


class CBCWatchVideoIE(CBCWatchBaseIE):
    IE_NAME = 'cbc.ca:watch:video'
    _VALID_URL = r'https?://api-cbc\.cloud\.clearleap\.com/cloffice/client/web/play/?\?.*?\bcontentId=(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        result = self._call_api(url, video_id)

        m3u8_url = xpath_text(result, 'url', fatal=True)
        formats = self._extract_m3u8_formats(re.sub(r'/([^/]+)/[^/?]+\.m3u8', r'/\1/\1.m3u8', m3u8_url), video_id, 'mp4', fatal=False)
        if len(formats) < 2:
            formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        self._sort_formats(formats)

        info = {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }

        rss = xpath_element(result, 'rss')
        if rss:
            info.update(self._parse_rss_feed(rss)['entries'][0])
            del info['url']
            del info['_type']
            del info['ie_key']
        return info


class CBCWatchIE(CBCWatchBaseIE):
    IE_NAME = 'cbc.ca:watch'
    _VALID_URL = r'https?://watch\.cbc\.ca/(?:[^/]+/)+(?P<id>[0-9a-f-]+)'
    _TESTS = [{
        'url': 'http://watch.cbc.ca/doc-zone/season-6/customer-disservice/38e815a-009e3ab12e4',
        'info_dict': {
            'id': '38e815a-009e3ab12e4',
            'ext': 'mp4',
            'title': 'Customer (Dis)Service',
            'description': 'md5:8bdd6913a0fe03d4b2a17ebe169c7c87',
            'upload_date': '20160219',
            'timestamp': 1455840000,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
            'format': 'bestvideo',
        },
        'skip': 'Geo-restricted to Canada',
    }, {
        'url': 'http://watch.cbc.ca/arthur/all/1ed4b385-cd84-49cf-95f0-80f004680057',
        'info_dict': {
            'id': '1ed4b385-cd84-49cf-95f0-80f004680057',
            'title': 'Arthur',
            'description': 'Arthur, the sweetest 8-year-old aardvark, and his pals solve all kinds of problems with humour, kindness and teamwork.',
        },
        'playlist_mincount': 30,
        'skip': 'Geo-restricted to Canada',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        rss = self._call_api('web/browse/' + video_id, video_id)
        return self._parse_rss_feed(rss)
