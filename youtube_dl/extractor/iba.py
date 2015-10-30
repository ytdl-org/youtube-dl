# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor


class IBAIE(InfoExtractor):
    _VALID_URL = r'http://www.iba.org.il/program.aspx\?scode=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.iba.org.il/program.aspx?scode=1937161',
        'md5': 'c5e52070148cafabf4487e79659eab97',
        'info_dict': {
            'id': '1937161',
            'ext': 'mp4',
            'title': u"התסריטאי ע` 1     פרק 2",
            'description' : 'md5:17e5a704a4bf79c5154cd5fd52d27c0b',
            'thumbnail': 're:^http://www.iba.org.il/pictures/p\d+\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vimmiId = self._search_regex(r"<div id='playerUrl' class='hidden'>([^<]+)</div>", webpage, 'vimmiId')
        playerExt = self._search_regex(r"<div id='playerExt' class='hidden'>([^<]+)</div>", webpage, 'playerExt')

        metaUrl = 'http://iba-metadata-rr-d.vidnt.com/vod/vod/%s/hls/metadata.xml' % (vimmiId)
        metadata = self._download_xml(metaUrl, video_id, note='Downloading metadata', errnote='Unable to download metadata')

        title = metadata.find('Title').text
        description = metadata.find('Description').text
        duration = int(metadata.find('Duration').text)
        urls = metadata.findall('.//FileURL')

        formats = []
        for url in urls:

            f = {
                'tbr': int(url.get('bitrate')),
                'width': int(url.get('width')),
                'height': int(url.get('height')),
                'url': url.text,
                'ext': playerExt,
            }

            formats.append(f)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
        }
