import json
import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_request,

    ExtractorError,
)


class MixcloudIE(InfoExtractor):
    _WORKING = False # New API, but it seems good http://www.mixcloud.com/developers/documentation/
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([\w\d-]+)/([\w\d-]+)'
    IE_NAME = u'mixcloud'

    def report_download_json(self, file_id):
        """Report JSON download."""
        self.to_screen(u'Downloading json')

    def get_urls(self, jsonData, fmt, bitrate='best'):
        """Get urls from 'audio_formats' section in json"""
        try:
            bitrate_list = jsonData[fmt]
            if bitrate is None or bitrate == 'best' or bitrate not in bitrate_list:
                bitrate = max(bitrate_list) # select highest

            url_list = jsonData[fmt][bitrate]
        except TypeError: # we have no bitrate info.
            url_list = jsonData[fmt]
        return url_list

    def check_urls(self, url_list):
        """Returns 1st active url from list"""
        for url in url_list:
            try:
                compat_urllib_request.urlopen(url)
                return url
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error):
                url = None

        return None

    def _print_formats(self, formats):
        print('Available formats:')
        for fmt in formats.keys():
            for b in formats[fmt]:
                try:
                    ext = formats[fmt][b][0]
                    print('%s\t%s\t[%s]' % (fmt, b, ext.split('.')[-1]))
                except TypeError: # we have no bitrate info
                    ext = formats[fmt][0]
                    print('%s\t%s\t[%s]' % (fmt, '??', ext.split('.')[-1]))
                    break

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        # extract uploader & filename from url
        uploader = mobj.group(1).decode('utf-8')
        file_id = uploader + "-" + mobj.group(2).decode('utf-8')

        # construct API request
        file_url = 'http://www.mixcloud.com/api/1/cloudcast/' + '/'.join(url.split('/')[-3:-1]) + '.json'
        # retrieve .json file with links to files
        request = compat_urllib_request.Request(file_url)
        try:
            self.report_download_json(file_url)
            jsonData = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve file: %s' % compat_str(err))

        # parse JSON
        json_data = json.loads(jsonData)
        player_url = json_data['player_swf_url']
        formats = dict(json_data['audio_formats'])

        req_format = self._downloader.params.get('format', None)

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        if req_format is None or req_format == 'best':
            for format_param in formats.keys():
                url_list = self.get_urls(formats, format_param)
                # check urls
                file_url = self.check_urls(url_list)
                if file_url is not None:
                    break # got it!
        else:
            if req_format not in formats:
                raise ExtractorError(u'Format is not available')

            url_list = self.get_urls(formats, req_format)
            file_url = self.check_urls(url_list)
            format_param = req_format

        return [{
            'id': file_id.decode('utf-8'),
            'url': file_url.decode('utf-8'),
            'uploader': uploader.decode('utf-8'),
            'upload_date': None,
            'title': json_data['name'],
            'ext': file_url.split('.')[-1].decode('utf-8'),
            'format': (format_param is None and u'NA' or format_param.decode('utf-8')),
            'thumbnail': json_data['thumbnail_url'],
            'description': json_data['description'],
            'player_url': player_url.decode('utf-8'),
        }]
