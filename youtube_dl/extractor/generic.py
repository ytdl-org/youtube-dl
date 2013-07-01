import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
)

class GenericIE(InfoExtractor):
    IE_DESC = u'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = u'generic'
    _TEST = {
        u'url': u'http://www.hodiho.fr/2013/02/regis-plante-sa-jeep.html',
        u'file': u'13601338388002.mp4',
        u'md5': u'85b90ccc9d73b4acd9138d3af4c27f89',
        u'info_dict': {
            u"uploader": u"www.hodiho.fr", 
            u"title": u"R\u00e9gis plante sa Jeep"
        }
    }

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        if not self._downloader.params.get('test', False):
            self._downloader.report_warning(u'Falling back on generic information extractor.')
        super(GenericIE, self).report_download_webpage(video_id)

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen(u'[redirect] Following redirect to %s' % new_url)

    def _test_redirect(self, url):
        """Check if it is a redirect, like url shorteners, in case return the new url."""
        class HeadRequest(compat_urllib_request.Request):
            def get_method(self):
                return "HEAD"

        class HEADRedirectHandler(compat_urllib_request.HTTPRedirectHandler):
            """
            Subclass the HTTPRedirectHandler to make it use our
            HeadRequest also on the redirected URL
            """
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if code in (301, 302, 303, 307):
                    newurl = newurl.replace(' ', '%20')
                    newheaders = dict((k,v) for k,v in req.headers.items()
                                      if k.lower() not in ("content-length", "content-type"))
                    return HeadRequest(newurl,
                                       headers=newheaders,
                                       origin_req_host=req.get_origin_req_host(),
                                       unverifiable=True)
                else:
                    raise compat_urllib_error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        class HTTPMethodFallback(compat_urllib_request.BaseHandler):
            """
            Fallback to GET if HEAD is not allowed (405 HTTP error)
            """
            def http_error_405(self, req, fp, code, msg, headers):
                fp.read()
                fp.close()

                newheaders = dict((k,v) for k,v in req.headers.items()
                                  if k.lower() not in ("content-length", "content-type"))
                return self.parent.open(compat_urllib_request.Request(req.get_full_url(),
                                                 headers=newheaders,
                                                 origin_req_host=req.get_origin_req_host(),
                                                 unverifiable=True))

        # Build our opener
        opener = compat_urllib_request.OpenerDirector()
        for handler in [compat_urllib_request.HTTPHandler, compat_urllib_request.HTTPDefaultErrorHandler,
                        HTTPMethodFallback, HEADRedirectHandler,
                        compat_urllib_request.HTTPErrorProcessor, compat_urllib_request.HTTPSHandler]:
            opener.add_handler(handler())

        response = opener.open(HeadRequest(url))
        if response is None:
            raise ExtractorError(u'Invalid URL protocol')
        new_url = response.geturl()

        if url == new_url:
            return False

        self.report_following_redirect(new_url)
        return new_url

    def _real_extract(self, url):
        new_url = self._test_redirect(url)
        if new_url: return [self.url_result(new_url)]

        video_id = url.split('/')[-1]
        try:
            webpage = self._download_webpage(url, video_id)
        except ValueError:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            raise ExtractorError(u'Invalid URL: %s' % url)

        self.report_extraction(video_id)
        # Start with something easy: JW Player in SWFObject
        mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit
            mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit: JWPlayer JS loader
            mobj = re.search(r'[^A-Za-z0-9]?file["\']?:\s*["\'](http[^\'"&]*)', webpage)
        if mobj is None:
            # Try to find twitter cards info
            mobj = re.search(r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage)
        if mobj is None:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them (eg.: statigr.am)
            m_video_type = re.search(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                mobj = re.search(r'<meta.*?property="og:video".*?content="(.*?)"', webpage)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_url = compat_urllib_parse.unquote(mobj.group(1))
        video_id = os.path.basename(video_url)

        # here's a fun little line of code for you:
        video_extension = os.path.splitext(video_id)[1][1:]
        video_id = os.path.splitext(video_id)[0]

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, u'video title', default=u'video', flags=re.DOTALL)

        # video uploader is domain name
        video_uploader = self._search_regex(r'(?:https?://)?([^/]*)/.*',
            url, u'video uploader')

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension,
        }]
