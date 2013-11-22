# encoding: utf-8

import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,

    ExtractorError,
    smuggle_url,
    unescapeHTML,
)
from .brightcove import BrightcoveIE


class GenericIE(InfoExtractor):
    IE_DESC = u'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = u'generic'
    _TESTS = [
        {
            u'url': u'http://www.hodiho.fr/2013/02/regis-plante-sa-jeep.html',
            u'file': u'13601338388002.mp4',
            u'md5': u'6e15c93721d7ec9e9ca3fdbf07982cfd',
            u'info_dict': {
                u"uploader": u"www.hodiho.fr",
                u"title": u"R\u00e9gis plante sa Jeep"
            }
        },
        # embedded vimeo video
        {
            u'add_ie': ['Vimeo'],
            u'url': u'http://skillsmatter.com/podcast/home/move-semanticsperfect-forwarding-and-rvalue-references',
            u'file': u'22444065.mp4',
            u'md5': u'2903896e23df39722c33f015af0666e2',
            u'info_dict': {
                u'title': u'ACCU 2011: Move Semantics,Perfect Forwarding, and Rvalue references- Scott Meyers- 13/04/2011',
                u"uploader_id": u"skillsmatter",
                u"uploader": u"Skills Matter",
            }
        },
        # bandcamp page with custom domain
        {
            u'add_ie': ['Bandcamp'],
            u'url': u'http://bronyrock.com/track/the-pony-mash',
            u'file': u'3235767654.mp3',
            u'info_dict': {
                u'title': u'The Pony Mash',
                u'uploader': u'M_Pallante',
            },
            u'skip': u'There is a limit of 200 free downloads / month for the test song',
        },
        # embedded brightcove video
        # it also tests brightcove videos that need to set the 'Referer' in the
        # http requests
        {
            u'add_ie': ['Brightcove'],
            u'url': u'http://www.bfmtv.com/video/bfmbusiness/cours-bourse/cours-bourse-l-analyse-technique-154522/',
            u'info_dict': {
                u'id': u'2765128793001',
                u'ext': u'mp4',
                u'title': u'Le cours de bourse : l’analyse technique',
                u'description': u'md5:7e9ad046e968cb2d1114004aba466fd9',
                u'uploader': u'BFM BUSINESS',
            },
            u'params': {
                u'skip_download': True,
            },
        },
    ]

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
        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
            return self.url_result('http://' + url)

        try:
            new_url = self._test_redirect(url)
            if new_url:
                return [self.url_result(new_url)]
        except compat_urllib_error.HTTPError:
            # This may be a stupid server that doesn't like HEAD, our UA, or so
            pass

        video_id = url.split('/')[-1]
        try:
            webpage = self._download_webpage(url, video_id)
        except ValueError:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            raise ExtractorError(u'Failed to download URL: %s' % url)

        self.report_extraction(video_id)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, u'video title', default=u'video', flags=re.DOTALL)

        # Look for BrightCove:
        bc_url = BrightcoveIE._extract_brightcove_url(webpage)
        if bc_url is not None:
            self.to_screen(u'Brightcove video detected.')
            return self.url_result(bc_url, 'Brightcove')

        # Look for embedded Vimeo player
        mobj = re.search(
            r'<iframe[^>]+?src="(https?://player.vimeo.com/video/.+?)"', webpage)
        if mobj:
            player_url = unescapeHTML(mobj.group(1))
            surl = smuggle_url(player_url, {'Referer': url})
            return self.url_result(surl, 'Vimeo')

        # Look for embedded YouTube player
        matches = re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?youtube.com/embed/.+?)\1', webpage)
        if matches:
            urlrs = [self.url_result(unescapeHTML(tuppl[1]), 'Youtube')
                     for tuppl in matches]
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for Bandcamp pages with custom domain
        mobj = re.search(r'<meta property="og:url"[^>]*?content="(.*?bandcamp\.com.*?)"', webpage)
        if mobj is not None:
            burl = unescapeHTML(mobj.group(1))
            # Don't set the extractor because it can be a track url or an album
            return self.url_result(burl)

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
            # HTML5 video
            mobj = re.search(r'<video[^<]*(?:>.*?<source.*?)? src="([^"]+)"', webpage, flags=re.DOTALL)
        if mobj is None:
            raise ExtractorError(u'Unsupported URL: %s' % url)

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            raise ExtractorError(u'Did not find a valid video URL at %s' % url)

        video_url = mobj.group(1)
        video_url = compat_urlparse.urljoin(url, video_url)
        video_id = compat_urllib_parse.unquote(os.path.basename(video_url))

        # here's a fun little line of code for you:
        video_extension = os.path.splitext(video_id)[1][1:]
        video_id = os.path.splitext(video_id)[0]

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
