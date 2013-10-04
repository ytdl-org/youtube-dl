# coding: utf-8

import re
import xml.etree.ElementTree
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    ExtractorError,
    find_xpath_attr,
)

class ORFIE(InfoExtractor):
    _VALID_URL = r'https?://tvthek.orf.at/(programs/.+?/episodes|topics/.+?)/(?P<id>\d+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        webpage = self._download_webpage(url, playlist_id)

        flash_xml = self._search_regex('ORF.flashXML = \'(.+?)\'', webpage, u'flash xml')
        flash_xml = compat_urlparse.parse_qs('xml='+flash_xml)['xml'][0]
        flash_config = xml.etree.ElementTree.fromstring(flash_xml.encode('utf-8'))
        playlist_json = self._search_regex(r'playlist\': \'(\[.*?\])\'', webpage, u'playlist').replace(r'\"','"')
        playlist = json.loads(playlist_json)

        videos = []
        ns = '{http://tempuri.org/XMLSchema.xsd}'
        xpath = '%(ns)sPlaylist/%(ns)sItems/%(ns)sItem' % {'ns': ns}
        webpage_description = self._og_search_description(webpage)
        for (i, (item, info)) in enumerate(zip(flash_config.findall(xpath), playlist), 1):
            # Get best quality url
            rtmp_url = None
            for q in ['Q6A', 'Q4A', 'Q1A']:
                video_url = find_xpath_attr(item, '%sVideoUrl' % ns, 'quality', q)
                if video_url is not None:
                    rtmp_url = video_url.text
                    break
            if rtmp_url is None:
                raise ExtractorError(u'Couldn\'t get video url: %s' % info['id'])
            description = self._html_search_regex(
                r'id="playlist_entry_%s".*?<p>(.*?)</p>' % i, webpage,
                u'description', default=webpage_description, flags=re.DOTALL)
            videos.append({
                '_type': 'video',
                'id': info['id'],
                'title': info['title'],
                'url': rtmp_url,
                'ext': 'flv',
                'description': description,
                })

        return videos
