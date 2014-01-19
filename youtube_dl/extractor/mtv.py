import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    ExtractorError,
)

def _media_xml_tag(tag):
    return '{http://search.yahoo.com/mrss/}%s' % tag


class MTVServicesInfoExtractor(InfoExtractor):
    @staticmethod
    def _id_from_uri(uri):
        return uri.split(':')[-1]

    # This was originally implemented for ComedyCentral, but it also works here
    @staticmethod
    def _transform_rtmp_url(rtmp_video_url):
        m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp\..+?/.*)$', rtmp_video_url)
        if not m:
            return rtmp_video_url
        base = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=1+_pxI0=Ripod-h264+_pxL0=undefined+_pxM0=+_pxK=18639+_pxE=mp4/44620/mtvnorigin/'
        return base + m.group('finalid')

    def _get_thumbnail_url(self, uri, itemdoc):
        search_path = '%s/%s' % (_media_xml_tag('group'), _media_xml_tag('thumbnail'))
        thumb_node = itemdoc.find(search_path)
        if thumb_node is None:
            return None
        else:
            return thumb_node.attrib['url']

    def _extract_video_formats(self, metadataXml):
        if '/error_country_block.swf' in metadataXml:
            raise ExtractorError(u'This video is not available from your country.', expected=True)
        mdoc = xml.etree.ElementTree.fromstring(metadataXml.encode('utf-8'))

        formats = []
        for rendition in mdoc.findall('.//rendition'):
            try:
                _, _, ext = rendition.attrib['type'].partition('/')
                rtmp_video_url = rendition.find('./src').text
                formats.append({'ext': ext,
                                'url': self._transform_rtmp_url(rtmp_video_url),
                                'format_id': rendition.get('bitrate'),
                                'width': int(rendition.get('width')),
                                'height': int(rendition.get('height')),
                                })
            except (KeyError, TypeError):
                raise ExtractorError('Invalid rendition field.')
        return formats

    def _get_video_info(self, itemdoc):
        uri = itemdoc.find('guid').text
        video_id = self._id_from_uri(uri)
        self.report_extraction(video_id)
        mediagen_url = itemdoc.find('%s/%s' % (_media_xml_tag('group'), _media_xml_tag('content'))).attrib['url']
        # Remove the templates, like &device={device}
        mediagen_url = re.sub(r'&[^=]*?={.*?}(?=(&|$))', u'', mediagen_url)
        if 'acceptMethods' not in mediagen_url:
            mediagen_url += '&acceptMethods=fms'
        mediagen_page = self._download_webpage(mediagen_url, video_id,
                                               u'Downloading video urls')

        description_node = itemdoc.find('description')
        if description_node is not None:
            description = description_node.text.strip()
        else:
            description = None

        return {
            'title': itemdoc.find('title').text,
            'formats': self._extract_video_formats(mediagen_page),
            'id': video_id,
            'thumbnail': self._get_thumbnail_url(uri, itemdoc),
            'description': description,
        }

    def _get_videos_info(self, uri):
        video_id = self._id_from_uri(uri)
        data = compat_urllib_parse.urlencode({'uri': uri})

        def fix_ampersand(s):
            """ Fix unencoded ampersand in XML """
            return s.replace(u'& ', '&amp; ')
        idoc = self._download_xml(
            self._FEED_URL + '?' + data, video_id,
            u'Downloading info', transform_source=fix_ampersand)
        return [self._get_video_info(item) for item in idoc.findall('.//item')]


class MTVIE(MTVServicesInfoExtractor):
    _VALID_URL = r'''(?x)^https?://
        (?:(?:www\.)?mtv\.com/videos/.+?/(?P<videoid>[0-9]+)/[^/]+$|
           m\.mtv\.com/videos/video\.rbml\?.*?id=(?P<mgid>[^&]+))'''

    _FEED_URL = 'http://www.mtv.com/player/embed/AS3/rss/'

    _TESTS = [
        {
            u'url': u'http://www.mtv.com/videos/misc/853555/ours-vh1-storytellers.jhtml',
            u'file': u'853555.mp4',
            u'md5': u'850f3f143316b1e71fa56a4edfd6e0f8',
            u'info_dict': {
                u'title': u'Taylor Swift - "Ours (VH1 Storytellers)"',
                u'description': u'Album: Taylor Swift performs "Ours" for VH1 Storytellers at Harvey Mudd College.',
            },
        },
        {
            u'add_ie': ['Vevo'],
            u'url': u'http://www.mtv.com/videos/taylor-swift/916187/everything-has-changed-ft-ed-sheeran.jhtml',
            u'file': u'USCJY1331283.mp4',
            u'md5': u'73b4e7fcadd88929292fe52c3ced8caf',
            u'info_dict': {
                u'title': u'Everything Has Changed',
                u'upload_date': u'20130606',
                u'uploader': u'Taylor Swift',
            },
            u'skip': u'VEVO is only available in some countries',
        },
    ]

    def _get_thumbnail_url(self, uri, itemdoc):
        return 'http://mtv.mtvnimages.com/uri/' + uri

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        uri = mobj.groupdict().get('mgid')
        if uri is None:
            webpage = self._download_webpage(url, video_id)
    
            # Some videos come from Vevo.com
            m_vevo = re.search(r'isVevoVideo = true;.*?vevoVideoId = "(.*?)";',
                               webpage, re.DOTALL)
            if m_vevo:
                vevo_id = m_vevo.group(1);
                self.to_screen(u'Vevo video detected: %s' % vevo_id)
                return self.url_result('vevo:%s' % vevo_id, ie='Vevo')
    
            uri = self._html_search_regex(r'/uri/(.*?)\?', webpage, u'uri')
        return self._get_videos_info(uri)
