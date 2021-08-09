from __future__ import unicode_literals

import re
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import urljoin

from .mtv import MTVServicesInfoExtractor


class ComedyCentralIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cc\.com/(?:episodes|video(?:-clips)?|collection-playlist/[0-9a-z]+/[^/]+)/(?P<id>[0-9a-z]{6})'
    _FEED_URL = 'http://comedycentral.com/feeds/mrss/'

    _TESTS = [{
        'url': 'http://www.cc.com/video-clips/5ke9v2/the-daily-show-with-trevor-noah-doc-rivers-and-steve-ballmer---the-nba-player-strike',
        'md5': '58e7caf5c7c0c865d9d79f7d151e5090',
        'info_dict': {
            'id': '89ccc86e-1b02-4f83-b0c9-1d9592ecd025',
            'ext': 'mp4',
            'title': 'The Daily Show with Trevor Noah|August 28, 2020|25|25149|Doc Rivers and Steve Ballmer - The NBA Player Strike',
            'description': 'md5:5334307c433892b85f4f5e5ac9ef7498',
            'timestamp': 1598670000,
            'upload_date': '20200829',
        },
        'params': {
            'hls_prefer_native': False,
        },
    }, {
        'url': 'http://www.cc.com/episodes/pnzzci/drawn-together--american-idol--parody-clip-show-season-3-ep-314',
        'only_matching': True,
    }, {
        'url': 'https://www.cc.com/video/k3sdvm/the-daily-show-with-jon-stewart-exclusive-the-fourth-estate',
        'only_matching': True,
    }, {
        'url': 'https://www.cc.com/collection-playlist/8b7hw5/the-daily-shows-summer-exclusives/o2qny3',
        'info_dict': {
            'id': '2f56e756-91ec-4d68-8799-e3b710e360e4',
            'ext': 'mp4',
            'title': 'The Daily Show with Trevor Noah|August 4, 2021|26|NO-EPISODE#|Hottest Take - The Olympics',
            'description': 'md5:104484314a4cba36d8c62b094523efc8',
            'timestamp': 1628125200,
            'upload_date': '20210805',
        },
        'params': {
            'hls_prefer_native': False,
        },
    }, ]


class ComedyCentralTVIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?comedycentral\.tv/folgen/(?P<id>[0-9a-z]{6})'
    _TESTS = [{
        'url': 'https://www.comedycentral.tv/folgen/pxdpec/josh-investigates-klimawandel-staffel-1-ep-1',
        'info_dict': {
            'id': '15907dc3-ec3c-11e8-a442-0e40cf2fc285',
            'ext': 'mp4',
            'title': 'Josh Investigates',
            'description': 'Steht uns das Ende der Welt bevor?',
        },
    }]
    _FEED_URL = 'http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed'
    _GEO_COUNTRIES = ['DE']

    def _get_feed_query(self, uri):
        return {
            'accountOverride': 'intl.mtvi.com',
            'arcEp': 'web.cc.tv',
            'ep': 'b9032c3a',
            'imageEp': 'web.cc.tv',
            'mgid': uri,
        }


class ComedyCentralCollectionIE(ComedyCentralIE):
    _VALID_URL = r'https?://(?:www\.)?cc\.com/collections/(?P<id>[0-9a-z]{6})(?:/[^/]*)?'
    _TESTS = [{
        'url': 'https://www.cc.com/collections/8b7hw5/the-daily-show-s-summer-exclusives',
        'info_dict': {
            'id': '8b7hw5',
            'title': "The Daily Show's Summer Exclusives",
            'description': 'md5:ae65028fcf8438e65f1c98099119fe6d',
        },
        'playlist_mincount': 11,
    }, ]
    _CLIP_IE = 'ComedyCentral'

    # we need to know the redirected URL, so stash it in the extractor
    # strange that this hasn't been a general requirement
    def _request_webpage(self, url_or_request, video_id,
                         note=None, errnote=None, fatal=True, data=None,
                         headers={}, query={}, expected_status=None):
        urlh = super(ComedyCentralCollectionIE, self)._request_webpage(
            url_or_request, video_id, note, errnote, fatal,
            data, headers, query, expected_status)
        if urlh is not False:
            self._url = urlh.geturl()
        elif isinstance(url_or_request, compat_str):
            self._url = url_or_request
        else:
            self._url = url_or_request.get_full_url()
        return urlh

    def _get_clip_id(self, url):
        return None

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        url = self._url
        clip_id = self._get_clip_id(url)
        if clip_id:
            url = url.rstrip(clip_id)
        else:
            url = url.replace('/collections/', '/collection-playlist/')
        path = compat_urlparse.urlparse(url).path
        if path.endswith('/'):
            path = path[:-1]
        clip_urls = re.finditer(
            r'<a\s?[^>]*?href\s*=\s*"(?P<link>%s/(?P<id>[0-9a-z]{6}))"[^<]*>' % path,
            webpage)
        playlist_title = (self._html_search_meta('twitter:title', webpage, 'title')
                          or self._og_search_title(webpage, display_name='title')
                          or self._html_search_regex(r'<title\s?[^>]*>([^<]+)</',
                                                     webpage, 'title', default=None))
        playlist_desc = (self._html_search_meta(('description', 'twitter:description'), webpage)
                         or self._og_search_description(webpage, display_name='description'))
        pl = self.playlist_from_matches(clip_urls, playlist_id, playlist_title,
                                        lambda m: urljoin(url, m.group('link')),
                                        self._CLIP_IE)
        if pl:
            pl['description'] = playlist_desc
            return pl


class ComedyCentralPlaylistIE(ComedyCentralCollectionIE):
    _VALID_URL = r'https?://(?:www\.)?cc\.com/playlists/(?P<id>[0-9a-z]{6})(?:/(?:[^/]+(?:/(?P<clip_id>[0-9a-z]{6})?)?)?)?'
    _TESTS = [{
        'url': 'https://www.cc.com/playlists/mym6e5/corporate-working-nine-to-five',
        'info_dict': {
            'id': 'mym6e5',
            'title': 'Coffee Break - Corporate | Comedy Central US',
            'description': 'md5:89bc6e8e983ad34ded85af84108f6ea8',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://www.cc.com/playlists/mym6e5/corporate-working-nine-to-five/dm8ekc',
        'only_matching': True,
    }, ]

    def _get_clip_id(self, url):
        mobj = re.match(self._VALID_URL, url)
        return mobj.group('clip_id')

    def _real_initialize(self):
        self._CLIP_IE = self.IE_NAME

    def _real_extract(self, url):
        if self._get_clip_id(url):
            return ComedyCentralIE._real_extract(self, url)
        playlist_id = self._match_id(url)
        if self._downloader.params.get('noplaylist', False):
            _ = self._download_webpage(url, playlist_id)
            if self._get_clip_id(self._url):
                self.to_screen(
                    'Downloading just the "now playing" clip because of --no-playlist')
                return self.url_result(self._url, self._CLIP_IE, playlist_id)
        return super(ComedyCentralPlaylistIE, self)._real_extract(url)
