import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    unescapeHTML,
    determine_ext,
    ExtractorError,
)


class XHamsterIE(InfoExtractor):
    """Information Extractor for xHamster"""
    _VALID_URL = r'(?:http://)?(?:www\.)?xhamster\.com/movies/(?P<id>[0-9]+)/(?P<seo>.+?)\.html(?:\?.*)?'
    _TESTS = [{
        u'url': u'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
        u'file': u'1509445.flv',
        u'md5': u'9f48e0e8d58e3076bb236ff412ab62fa',
        u'info_dict': {
            u"upload_date": u"20121014", 
            u"uploader_id": u"Ruseful2011", 
            u"title": u"FemaleAgent Shy beauty takes the bait",
            u"age_limit": 18,
        }
    },
    {
        u'url': u'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
        u'file': u'2221348.flv',
        u'md5': u'e767b9475de189320f691f49c679c4c7',
        u'info_dict': {
            u"upload_date": u"20130914",
            u"uploader_id": u"jojo747400",
            u"title": u"Britney Spears  Sexy Booty",
            u"age_limit": 18,
        }
    }]

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        seo = mobj.group('seo')
        mrss_url = 'http://xhamster.com/movies/%s/%s.html?hd' % (video_id, seo)
        webpage = self._download_webpage(mrss_url, video_id)

        mobj = re.search(r'\'srv\': \'(?P<server>[^\']*)\',\s*\'file\': \'(?P<file>[^\']+)\',', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract media URL')
        if len(mobj.group('server')) == 0:
            video_url = compat_urllib_parse.unquote(mobj.group('file'))
        else:
            video_url = mobj.group('server')+'/key='+mobj.group('file')

        video_title = self._html_search_regex(r'<title>(?P<title>.+?) - xHamster\.com</title>',
            webpage, u'title')

        # Only a few videos have an description
        mobj = re.search('<span>Description: </span>(?P<description>[^<]+)', webpage)
        if mobj:
            video_description = unescapeHTML(mobj.group('description'))
        else:
            video_description = None

        mobj = re.search(r'hint=\'(?P<upload_date_Y>[0-9]{4})-(?P<upload_date_m>[0-9]{2})-(?P<upload_date_d>[0-9]{2}) [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{3,4}\'', webpage)
        if mobj:
            video_upload_date = mobj.group('upload_date_Y')+mobj.group('upload_date_m')+mobj.group('upload_date_d')
        else:
            video_upload_date = None
            self._downloader.report_warning(u'Unable to extract upload date')

        video_uploader_id = self._html_search_regex(r'<a href=\'/user/[^>]+>(?P<uploader_id>[^<]+)',
            webpage, u'uploader id', default=u'anonymous')

        video_thumbnail = self._search_regex(r'\'image\':\'(?P<thumbnail>[^\']+)\'',
            webpage, u'thumbnail', fatal=False)

        age_limit = self._rta_search(webpage)

        return [{
            'id':       video_id,
            'url':      video_url,
            'ext':      determine_ext(video_url),
            'title':    video_title,
            'description': video_description,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        }]
