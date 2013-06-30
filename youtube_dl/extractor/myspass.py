import os.path
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,

    ExtractorError,
)


class MySpassIE(InfoExtractor):
    _VALID_URL = r'http://www.myspass.de/.*'
    _TEST = {
        u'url': u'http://www.myspass.de/myspass/shows/tvshows/absolute-mehrheit/Absolute-Mehrheit-vom-17022013-Die-Highlights-Teil-2--/11741/',
        u'file': u'11741.mp4',
        u'md5': u'0b49f4844a068f8b33f4b7c88405862b',
        u'info_dict': {
            u"description": u"Wer kann in die Fu\u00dfstapfen von Wolfgang Kubicki treten und die Mehrheit der Zuschauer hinter sich versammeln? Wird vielleicht sogar die Absolute Mehrheit geknackt und der Jackpot von 200.000 Euro mit nach Hause genommen?", 
            u"title": u"Absolute Mehrheit vom 17.02.2013 - Die Highlights, Teil 2"
        }
    }

    def _real_extract(self, url):
        META_DATA_URL_TEMPLATE = 'http://www.myspass.de/myspass/includes/apps/video/getvideometadataxml.php?id=%s'

        # video id is the last path element of the URL
        # usually there is a trailing slash, so also try the second but last
        url_path = compat_urllib_parse_urlparse(url).path
        url_parent_path, video_id = os.path.split(url_path)
        if not video_id:
            _, video_id = os.path.split(url_parent_path)

        # get metadata
        metadata_url = META_DATA_URL_TEMPLATE % video_id
        metadata_text = self._download_webpage(metadata_url, video_id)
        metadata = xml.etree.ElementTree.fromstring(metadata_text.encode('utf-8'))

        # extract values from metadata
        url_flv_el = metadata.find('url_flv')
        if url_flv_el is None:
            raise ExtractorError(u'Unable to extract download url')
        video_url = url_flv_el.text
        extension = os.path.splitext(video_url)[1][1:]
        title_el = metadata.find('title')
        if title_el is None:
            raise ExtractorError(u'Unable to extract title')
        title = title_el.text
        format_id_el = metadata.find('format_id')
        if format_id_el is None:
            format = 'mp4'
        else:
            format = format_id_el.text
        description_el = metadata.find('description')
        if description_el is not None:
            description = description_el.text
        else:
            description = None
        imagePreview_el = metadata.find('imagePreview')
        if imagePreview_el is not None:
            thumbnail = imagePreview_el.text
        else:
            thumbnail = None
        info = {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': extension,
            'format': format,
            'thumbnail': thumbnail,
            'description': description
        }
        return [info]
