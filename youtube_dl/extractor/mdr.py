from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MDRIE(InfoExtractor):
    _VALID_URL = r'^(?P<domain>https?://(?:www\.)?mdr\.de)/(?:.*)/(?P<type>video|audio)(?P<video_id>[^/_]+)(?:_|\.html)'

    # No tests, MDR regularily deletes its videos
    _TEST = {
        'url': 'http://www.mdr.de/fakt/video189002.html',
        'only_matching': True,
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('video_id')
        domain = m.group('domain')

        # determine title and media streams from webpage
        html = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h[12]>(.*?)</h[12]>', html, 'title')
        xmlurl = self._search_regex(
            r'dataURL:\'(/(?:.+)/(?:video|audio)[0-9]+-avCustom.xml)', html, 'XML URL')

        doc = self._download_xml(domain + xmlurl, video_id)
        formats = []
        for a in doc.findall('./assets/asset'):
            url_el = a.find('.//progressiveDownloadUrl')
            if url_el is None:
                continue
            abr = int(a.find('bitrateAudio').text) // 1000
            media_type = a.find('mediaType').text
            format = {
                'abr': abr,
                'filesize': int(a.find('fileSize').text),
                'url': url_el.text,
            }

            vbr_el = a.find('bitrateVideo')
            if vbr_el is None:
                format.update({
                    'vcodec': 'none',
                    'format_id': '%s-%d' % (media_type, abr),
                })
            else:
                vbr = int(vbr_el.text) // 1000
                format.update({
                    'vbr': vbr,
                    'width': int(a.find('frameWidth').text),
                    'height': int(a.find('frameHeight').text),
                    'format_id': '%s-%d' % (media_type, vbr),
                })
            formats.append(format)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
