# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    find_xpath_attr,
    fix_xml_ampersands,
    compat_urlparse,
    compat_str,
    compat_urllib_request,
    compat_parse_qs,
    compat_urllib_parse_urlparse,

    determine_ext,
    ExtractorError,
    unsmuggle_url,
    unescapeHTML,
)


class BrightcoveIE(InfoExtractor):
    _VALID_URL = r'https?://.*brightcove\.com/(services|viewer).*?\?(?P<query>.*)'
    _FEDERATED_URL_TEMPLATE = 'http://c.brightcove.com/services/viewer/htmlFederated?%s'

    _TESTS = [
        {
            # From http://www.8tv.cat/8aldia/videos/xavier-sala-i-martin-aquesta-tarda-a-8-al-dia/
            'url': 'http://c.brightcove.com/services/viewer/htmlFederated?playerID=1654948606001&flashID=myExperience&%40videoPlayer=2371591881001',
            'md5': '5423e113865d26e40624dce2e4b45d95',
            'note': 'Test Brightcove downloads and detection in GenericIE',
            'info_dict': {
                'id': '2371591881001',
                'ext': 'mp4',
                'title': 'Xavier Sala i Martín: “Un banc que no presta és un banc zombi que no serveix per a res”',
                'uploader': '8TV',
                'description': 'md5:a950cc4285c43e44d763d036710cd9cd',
            }
        },
        {
            # From http://medianetwork.oracle.com/video/player/1785452137001
            'url': 'http://c.brightcove.com/services/viewer/htmlFederated?playerID=1217746023001&flashID=myPlayer&%40videoPlayer=1785452137001',
            'info_dict': {
                'id': '1785452137001',
                'ext': 'flv',
                'title': 'JVMLS 2012: Arrays 2.0 - Opportunities and Challenges',
                'description': 'John Rose speaks at the JVM Language Summit, August 1, 2012.',
                'uploader': 'Oracle',
            },
        },
        {
            # From http://mashable.com/2013/10/26/thermoelectric-bracelet-lets-you-control-your-body-temperature/
            'url': 'http://c.brightcove.com/services/viewer/federated_f9?&playerID=1265504713001&publisherID=AQ%7E%7E%2CAAABBzUwv1E%7E%2CxP-xFHVUstiMFlNYfvF4G9yFnNaqCw_9&videoID=2750934548001',
            'info_dict': {
                'id': '2750934548001',
                'ext': 'mp4',
                'title': 'This Bracelet Acts as a Personal Thermostat',
                'description': 'md5:547b78c64f4112766ccf4e151c20b6a0',
                'uploader': 'Mashable',
            },
        },
        {
            # test that the default referer works
            # from http://national.ballet.ca/interact/video/Lost_in_Motion_II/
            'url': 'http://link.brightcove.com/services/player/bcpid756015033001?bckey=AQ~~,AAAApYJi_Ck~,GxhXCegT1Dp39ilhXuxMJxasUhVNZiil&bctid=2878862109001',
            'info_dict': {
                'id': '2878862109001',
                'ext': 'mp4',
                'title': 'Lost in Motion II',
                'description': 'md5:363109c02998fee92ec02211bd8000df',
                'uploader': 'National Ballet of Canada',
            },
        },
        {
            # test flv videos served by akamaihd.net
            # From http://www.redbull.com/en/bike/stories/1331655643987/replay-uci-dh-world-cup-2014-from-fort-william
            'url': 'http://c.brightcove.com/services/viewer/htmlFederated?%40videoPlayer=ref%3ABC2996102916001&linkBaseURL=http%3A%2F%2Fwww.redbull.com%2Fen%2Fbike%2Fvideos%2F1331655630249%2Freplay-uci-fort-william-2014-dh&playerKey=AQ%7E%7E%2CAAAApYJ7UqE%7E%2Cxqr_zXk0I-zzNndy8NlHogrCb5QdyZRf&playerID=1398061561001#__youtubedl_smuggle=%7B%22Referer%22%3A+%22http%3A%2F%2Fwww.redbull.com%2Fen%2Fbike%2Fstories%2F1331655643987%2Freplay-uci-dh-world-cup-2014-from-fort-william%22%7D',
            # The md5 checksum changes on each download
            'info_dict': {
                'id': '2996102916001',
                'ext': 'flv',
                'title': 'UCI MTB World Cup 2014: Fort William, UK - Downhill Finals',
                'uploader': 'Red Bull TV',
                'description': 'UCI MTB World Cup 2014: Fort William, UK - Downhill Finals',
            },
        },
        {
            # playlist test
            # from http://support.brightcove.com/en/video-cloud/docs/playlist-support-single-video-players
            'url': 'http://c.brightcove.com/services/viewer/htmlFederated?playerID=3550052898001&playerKey=AQ%7E%7E%2CAAABmA9XpXk%7E%2C-Kp7jNgisre1fG5OdqpAFUTcs0lP_ZoL',
            'info_dict': {
                'title': 'Sealife',
            },
            'playlist_mincount': 7,
        },
    ]

    @classmethod
    def _build_brighcove_url(cls, object_str):
        """
        Build a Brightcove url from a xml string containing
        <object class="BrightcoveExperience">{params}</object>
        """

        # Fix up some stupid HTML, see https://github.com/rg3/youtube-dl/issues/1553
        object_str = re.sub(r'(<param name="[^"]+" value="[^"]+")>',
                            lambda m: m.group(1) + '/>', object_str)
        # Fix up some stupid XML, see https://github.com/rg3/youtube-dl/issues/1608
        object_str = object_str.replace('<--', '<!--')
        # remove namespace to simplify extraction
        object_str = re.sub(r'(<object[^>]*)(xmlns=".*?")', r'\1', object_str)
        object_str = fix_xml_ampersands(object_str)

        object_doc = xml.etree.ElementTree.fromstring(object_str.encode('utf-8'))

        fv_el = find_xpath_attr(object_doc, './param', 'name', 'flashVars')
        if fv_el is not None:
            flashvars = dict(
                (k, v[0])
                for k, v in compat_parse_qs(fv_el.attrib['value']).items())
        else:
            flashvars = {}

        def find_param(name):
            if name in flashvars:
                return flashvars[name]
            node = find_xpath_attr(object_doc, './param', 'name', name)
            if node is not None:
                return node.attrib['value']
            return None

        params = {}

        playerID = find_param('playerID')
        if playerID is None:
            raise ExtractorError('Cannot find player ID')
        params['playerID'] = playerID

        playerKey = find_param('playerKey')
        # Not all pages define this value
        if playerKey is not None:
            params['playerKey'] = playerKey
        # The three fields hold the id of the video
        videoPlayer = find_param('@videoPlayer') or find_param('videoId') or find_param('videoID')
        if videoPlayer is not None:
            params['@videoPlayer'] = videoPlayer
        linkBase = find_param('linkBaseURL')
        if linkBase is not None:
            params['linkBaseURL'] = linkBase
        data = compat_urllib_parse.urlencode(params)
        return cls._FEDERATED_URL_TEMPLATE % data

    @classmethod
    def _extract_brightcove_url(cls, webpage):
        """Try to extract the brightcove url from the webpage, returns None
        if it can't be found
        """
        urls = cls._extract_brightcove_urls(webpage)
        return urls[0] if urls else None

    @classmethod
    def _extract_brightcove_urls(cls, webpage):
        """Return a list of all Brightcove URLs from the webpage """

        url_m = re.search(
            r'<meta\s+property="og:video"\s+content="(https?://(?:secure|c)\.brightcove.com/[^"]+)"',
            webpage)
        if url_m:
            url = unescapeHTML(url_m.group(1))
            # Some sites don't add it, we can't download with this url, for example:
            # http://www.ktvu.com/videos/news/raw-video-caltrain-releases-video-of-man-almost/vCTZdY/
            if 'playerKey' in url or 'videoId' in url:
                return [url]

        matches = re.findall(
            r'''(?sx)<object
            (?:
                [^>]+?class=[\'"][^>]*?BrightcoveExperience.*?[\'"] |
                [^>]*?>\s*<param\s+name="movie"\s+value="https?://[^/]*brightcove\.com/
            ).+?</object>''',
            webpage)
        return [cls._build_brighcove_url(m) for m in matches]

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        # Change the 'videoId' and others field to '@videoPlayer'
        url = re.sub(r'(?<=[?&])(videoI(d|D)|bctid)', '%40videoPlayer', url)
        # Change bckey (used by bcove.me urls) to playerKey
        url = re.sub(r'(?<=[?&])bckey', 'playerKey', url)
        mobj = re.match(self._VALID_URL, url)
        query_str = mobj.group('query')
        query = compat_urlparse.parse_qs(query_str)

        videoPlayer = query.get('@videoPlayer')
        if videoPlayer:
            # We set the original url as the default 'Referer' header
            referer = smuggled_data.get('Referer', url)
            return self._get_video_info(
                videoPlayer[0], query_str, query, referer=referer)
        elif 'playerKey' in query:
            player_key = query['playerKey']
            return self._get_playlist_info(player_key[0])
        else:
            raise ExtractorError(
                'Cannot find playerKey= variable. Did you forget quotes in a shell invocation?',
                expected=True)

    def _get_video_info(self, video_id, query_str, query, referer=None):
        request_url = self._FEDERATED_URL_TEMPLATE % query_str
        req = compat_urllib_request.Request(request_url)
        linkBase = query.get('linkBaseURL')
        if linkBase is not None:
            referer = linkBase[0]
        if referer is not None:
            req.add_header('Referer', referer)
        webpage = self._download_webpage(req, video_id)

        error_msg = self._html_search_regex(
            r"<h1>We're sorry.</h1>([\s\n]*<p>.*?</p>)+", webpage,
            'error message', default=None)
        if error_msg is not None:
            raise ExtractorError(
                'brightcove said: %s' % error_msg, expected=True)

        self.report_extraction(video_id)
        info = self._search_regex(r'var experienceJSON = ({.*});', webpage, 'json')
        info = json.loads(info)['data']
        video_info = info['programmedContent']['videoPlayer']['mediaDTO']
        video_info['_youtubedl_adServerURL'] = info.get('adServerURL')

        return self._extract_video_info(video_info)

    def _get_playlist_info(self, player_key):
        info_url = 'http://c.brightcove.com/services/json/experience/runtime/?command=get_programming_for_experience&playerKey=%s' % player_key
        playlist_info = self._download_webpage(
            info_url, player_key, 'Downloading playlist information')

        json_data = json.loads(playlist_info)
        if 'videoList' not in json_data:
            raise ExtractorError('Empty playlist')
        playlist_info = json_data['videoList']
        videos = [self._extract_video_info(video_info) for video_info in playlist_info['mediaCollectionDTO']['videoDTOs']]

        return self.playlist_result(videos, playlist_id=playlist_info['id'],
                                    playlist_title=playlist_info['mediaCollectionDTO']['displayName'])

    def _extract_video_info(self, video_info):
        info = {
            'id': compat_str(video_info['id']),
            'title': video_info['displayName'].strip(),
            'description': video_info.get('shortDescription'),
            'thumbnail': video_info.get('videoStillURL') or video_info.get('thumbnailURL'),
            'uploader': video_info.get('publisherName'),
        }

        renditions = video_info.get('renditions')
        if renditions:
            formats = []
            for rend in renditions:
                url = rend['defaultURL']
                if not url:
                    continue
                ext = None
                if rend['remote']:
                    url_comp = compat_urllib_parse_urlparse(url)
                    if url_comp.path.endswith('.m3u8'):
                        formats.extend(
                            self._extract_m3u8_formats(url, info['id'], 'mp4'))
                        continue
                    elif 'akamaihd.net' in url_comp.netloc:
                        # This type of renditions are served through
                        # akamaihd.net, but they don't use f4m manifests
                        url = url.replace('control/', '') + '?&v=3.3.0&fp=13&r=FEEFJ&g=RTSJIMBMPFPB'
                        ext = 'flv'
                if ext is None:
                    ext = determine_ext(url)
                size = rend.get('size')
                formats.append({
                    'url': url,
                    'ext': ext,
                    'height': rend.get('frameHeight'),
                    'width': rend.get('frameWidth'),
                    'filesize': size if size != 0 else None,
                })
            self._sort_formats(formats)
            info['formats'] = formats
        elif video_info.get('FLVFullLengthURL') is not None:
            info.update({
                'url': video_info['FLVFullLengthURL'],
            })

        if self._downloader.params.get('include_ads', False):
            adServerURL = video_info.get('_youtubedl_adServerURL')
            if adServerURL:
                ad_info = {
                    '_type': 'url',
                    'url': adServerURL,
                }
                if 'url' in info:
                    return {
                        '_type': 'playlist',
                        'title': info['title'],
                        'entries': [ad_info, info],
                    }
                else:
                    return ad_info

        if 'url' not in info and not info.get('formats'):
            raise ExtractorError('Unable to extract video url for %s' % info['id'])
        return info
