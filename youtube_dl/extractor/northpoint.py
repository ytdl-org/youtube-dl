# coding: utf-8
from __future__ import unicode_literals

from .theplatform import ThePlatformIE


class NorthpointIE(ThePlatformIE):
    _VALID_URL = r'(?:http?://)?(?:www\.)?northpoint\.org/messages/[^/]+/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://northpoint.org/messages/three-things/what-makes-you-a-wonder/',
        'md5': '214af23fa75d0fae44298a5128c35d56',
        'info_dict': {
            'id': 'rosH7wGAB33s',
            'ext': 'mp4',
            'title': "Three Things I Learned from a Movie I Didn't Want to See - The Power Of Friendship",
            'series': "Three Things I Learned from a Movie I Didn't Want to See",
        }
    }]

    def _real_extract(self, url):

        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        playerCode = self._search_regex(r'playerCode\s*=\s*[\'"]([^\'"]+)', webpage, 'player Code')
        seriesPermalink = self._search_regex(r'series_permalink\s*:\s*[\'"]([^\'"]+)', webpage, 'series name')
        seriesJSON = self._download_json('http://northpoint.org/api/mma/details/channel/npcc/permalink/%s' % seriesPermalink, display_id)['messages']

        videoIDLink = ''
        videoIDLinkTemp = ''
        for serie in seriesJSON:
            videoIDLinkTemp = serie['hv_msg']['id']
            if serie['title'].lower() == display_id.replace('-', ' ').lower():
                videoIDLink = serie['hv_msg']['id']

        if not videoIDLink:
            videoIDLink = videoIDLinkTemp

        linkWebpage = self._download_webpage('http://player.theplatform.com/p/IfSiAC/' + playerCode + '/embed/select/' + videoIDLink, display_id)
        releaseUrl = self._search_regex(r'tp:releaseUrl\s*=\s*[\'"]([^\'"]+)', linkWebpage, 'release url')
        platformMetaData = self._search_regex(r'.*.com\/s\/\s*([^\n\r]*)[ˆ?]', releaseUrl, 'release url')
        theplatform_metadata = self._download_theplatform_metadata(platformMetaData, display_id)

        video_id = theplatform_metadata['pid']
        title = theplatform_metadata['title'][19:]
        series = theplatform_metadata['pl1$seriesName']

        formats, subtitles = self._extract_theplatform_smil(releaseUrl, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'subtitles': subtitles,
            'formats': formats,
            'series': series,
        }
