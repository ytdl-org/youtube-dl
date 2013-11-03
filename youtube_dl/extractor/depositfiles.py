import re
import os
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
)


class DepositFilesIE(InfoExtractor):
    """Information extractor for depositfiles.com"""

    _VALID_URL = r'(?:http://)?(?:\w+\.)?depositfiles\.com/(?:../(?#locale))?files/(.+)'

    def _real_extract(self, url):
        file_id = url.split('/')[-1]
        # Rebuild url in english locale
        url = 'http://depositfiles.com/en/files/' + file_id

        # Retrieve file webpage with 'Free download' button pressed
        free_download_indication = {'gateway_result' : '1'}
        request = compat_urllib_request.Request(url, compat_urllib_parse.urlencode(free_download_indication))
        try:
            self.report_download_webpage(file_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve file webpage: %s' % compat_str(err))

        # Search for the real file URL
        mobj = re.search(r'<form action="(http://fileshare.+?)"', webpage)
        if (mobj is None) or (mobj.group(1) is None):
            # Try to figure out reason of the error.
            mobj = re.search(r'<strong>(Attention.*?)</strong>', webpage, re.DOTALL)
            if (mobj is not None) and (mobj.group(1) is not None):
                restriction_message = re.sub('\s+', ' ', mobj.group(1)).strip()
                raise ExtractorError(u'%s' % restriction_message)
            else:
                raise ExtractorError(u'Unable to extract download URL from: %s' % url)

        file_url = mobj.group(1)
        file_extension = os.path.splitext(file_url)[1][1:]

        # Search for file title
        file_title = self._search_regex(r'<b title="(.*?)">', webpage, u'title')

        return [{
            'id':       file_id.decode('utf-8'),
            'url':      file_url.decode('utf-8'),
            'uploader': None,
            'upload_date':  None,
            'title':    file_title,
            'ext':      file_extension.decode('utf-8'),
        }]
