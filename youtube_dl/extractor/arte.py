import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    # This is used by the not implemented extractLiveStream method
    compat_urllib_parse,

    ExtractorError,
    unified_strdate,
)

class ArteTvIE(InfoExtractor):
    """
    There are two sources of video in arte.tv: videos.arte.tv and
    www.arte.tv/guide, the extraction process is different for each one.
    The videos expire in 7 days, so we can't add tests.
    """
    _EMISSION_URL = r'(?:http://)?www\.arte.tv/guide/(?P<lang>fr|de)/(?:(?:sendungen|emissions)/)?(?P<id>.*?)/(?P<name>.*?)(\?.*)?'
    _VIDEOS_URL = r'(?:http://)?videos.arte.tv/(?P<lang>fr|de)/.*-(?P<id>.*?).html'
    _LIVE_URL = r'index-[0-9]+\.html$'

    IE_NAME = u'arte.tv'

    @classmethod
    def suitable(cls, url):
        return any(re.match(regex, url) for regex in (cls._EMISSION_URL, cls._VIDEOS_URL))

    # TODO implement Live Stream
    # def extractLiveStream(self, url):
    #     video_lang = url.split('/')[-4]
    #     info = self.grep_webpage(
    #         url,
    #         r'src="(.*?/videothek_js.*?\.js)',
    #         0,
    #         [
    #             (1, 'url', u'Invalid URL: %s' % url)
    #         ]
    #     )
    #     http_host = url.split('/')[2]
    #     next_url = 'http://%s%s' % (http_host, compat_urllib_parse.unquote(info.get('url')))
    #     info = self.grep_webpage(
    #         next_url,
    #         r'(s_artestras_scst_geoFRDE_' + video_lang + '.*?)\'.*?' +
    #             '(http://.*?\.swf).*?' +
    #             '(rtmp://.*?)\'',
    #         re.DOTALL,
    #         [
    #             (1, 'path',   u'could not extract video path: %s' % url),
    #             (2, 'player', u'could not extract video player: %s' % url),
    #             (3, 'url',    u'could not extract video url: %s' % url)
    #         ]
    #     )
    #     video_url = u'%s/%s' % (info.get('url'), info.get('path'))

    def _real_extract(self, url):
        mobj = re.match(self._EMISSION_URL, url)
        if mobj is not None:
            name = mobj.group('name')
            lang = mobj.group('lang')
            # This is not a real id, it can be for example AJT for the news
            # http://www.arte.tv/guide/fr/emissions/AJT/arte-journal
            video_id = mobj.group('id')
            return self._extract_emission(url, video_id, lang)

        mobj = re.match(self._VIDEOS_URL, url)
        if mobj is not None:
            id = mobj.group('id')
            lang = mobj.group('lang')
            return self._extract_video(url, id, lang)

        if re.search(self._LIVE_URL, video_id) is not None:
            raise ExtractorError(u'Arte live streams are not yet supported, sorry')
            # self.extractLiveStream(url)
            # return

    def _extract_emission(self, url, video_id, lang):
        """Extract from www.arte.tv/guide"""
        json_url = 'http://org-www.arte.tv/papi/tvguide/videos/stream/player/F/%s_PLUS7-F/ALL/ALL.json' % video_id

        json_info = self._download_webpage(json_url, video_id, 'Downloading info json')
        self.report_extraction(video_id)
        info = json.loads(json_info)
        player_info = info['videoJsonPlayer']

        info_dict = {'id': player_info['VID'],
                     'title': player_info['VTI'],
                     'description': player_info['VDE'],
                     'upload_date': unified_strdate(player_info['VDA'].split(' ')[0]),
                     'thumbnail': player_info['programImage'],
                     'ext': 'flv',
                     }

        formats = player_info['VSR'].values()
        def _match_lang(f):
            # Return true if that format is in the language of the url
            if lang == 'fr':
                l = 'F'
            elif lang == 'de':
                l = 'A'
            regexes = [r'VO?%s' % l, r'V%s-ST.' % l]
            return any(re.match(r, f['versionCode']) for r in regexes)
        # Some formats may not be in the same language as the url
        formats = filter(_match_lang, formats)
        # We order the formats by quality
        formats = sorted(formats, key=lambda f: int(f['height']))
        # Pick the best quality
        format_info = formats[-1]
        if format_info['mediaType'] == u'rtmp':
            info_dict['url'] = format_info['streamer']
            info_dict['play_path'] = 'mp4:' + format_info['url']
        else:
            info_dict['url'] = format_info['url']

        return info_dict

    def _extract_video(self, url, video_id, lang):
        """Extract from videos.arte.tv"""
        ref_xml_url = url.replace('/videos/', '/do_delegate/videos/')
        ref_xml_url = ref_xml_url.replace('.html', ',view,asPlayerXml.xml')
        ref_xml = self._download_webpage(ref_xml_url, video_id, note=u'Downloading metadata')
        ref_xml_doc = xml.etree.ElementTree.fromstring(ref_xml)
        config_node = ref_xml_doc.find('.//video[@lang="%s"]' % lang)
        config_xml_url = config_node.attrib['ref']
        config_xml = self._download_webpage(config_xml_url, video_id, note=u'Downloading configuration')

        video_urls = list(re.finditer(r'<url quality="(?P<quality>.*?)">(?P<url>.*?)</url>', config_xml))
        def _key(m):
            quality = m.group('quality')
            if quality == 'hd':
                return 2
            else:
                return 1
        # We pick the best quality
        video_urls = sorted(video_urls, key=_key)
        video_url = list(video_urls)[-1].group('url')
        
        title = self._html_search_regex(r'<name>(.*?)</name>', config_xml, 'title')
        thumbnail = self._html_search_regex(r'<firstThumbnailUrl>(.*?)</firstThumbnailUrl>',
                                            config_xml, 'thumbnail')
        return {'id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'url': video_url,
                'ext': 'flv',
                }
