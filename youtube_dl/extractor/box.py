# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    parse_iso8601,
    try_get,
    update_url_query,
)


class BoxIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<prefix>(?:[^.]+\.)?)app\.box\.com/s/(?P<shared_name>[^/]+)(?:/file/(?P<id>\d+))?'
    _TEST = {
        'url': 'https://mlssoccer.app.box.com/s/0evd2o3e08l60lr4ygukepvnkord1o1x/file/510727257538',
        'md5': '1f81b2fd3960f38a40a3b8823e5fcd43',
        'info_dict': {
            'id': '510727257538',
            'ext': 'mp4',
            'title': 'Garber   St. Louis will be 28th MLS team  +scarving.mp4',
            'uploader': 'MLS Video',
            'timestamp': 1566320259,
            'upload_date': '20190820',
            'uploader_id': '235196876',
        }
    }

    def _real_extract(self, url):
        prefix, shared_name, file_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, file_id)
        if not file_id:
            file_id = re.search(r'"typedID":\s*"f_(\d+)"', webpage).group(1)
        request_token = self._parse_json(self._search_regex(
            r'Box\.config\s*=\s*({.+?});', webpage,
            'Box config'), file_id)['requestToken']
        access_token = self._download_json(
            'https://' + prefix + 'app.box.com/app-api/enduserapp/elements/tokens', file_id,
            'Downloading token JSON metadata',
            data=json.dumps({'fileIDs': [file_id]}).encode(), headers={
                'Content-Type': 'application/json',
                'X-Request-Token': request_token,
                'X-Box-EndUser-API': 'sharedName=' + shared_name,
            })[file_id]['read']
        shared_link = 'https://' + prefix + 'app.box.com/s/' + shared_name
        f = self._download_json(
            'https://api.box.com/2.0/files/' + file_id, file_id,
            'Downloading file JSON metadata', headers={
                'Authorization': 'Bearer ' + access_token,
                'BoxApi': 'shared_link=' + shared_link,
                'X-Rep-Hints': '[dash]',  # TODO: extract `hls` formats
            }, query={
                'fields': 'permissions,authenticated_download_url,created_at,created_by,description,extension,is_download_available,name,representations,size'
            })
        title = f['name']

        query = {
            'access_token': access_token,
            'shared_link': shared_link
        }

        formats = []

        for entry in (try_get(f, lambda x: x['representations']['entries'], list) or []):
            entry_url_template = try_get(
                entry, lambda x: x['content']['url_template'])
            if not entry_url_template:
                continue
            representation = entry.get('representation')
            if representation == 'dash':
                extracted = self._extract_mpd_formats(
                    entry_url_template.replace('{+asset_path}', 'manifest.mpd'),
                    file_id, query=query)
                for extracted_format in extracted:
                    for fragment in extracted_format['fragments']:
                        fragment['path'] = update_url_query(fragment['path'], query)
                formats.extend(extracted)

        authenticated_download_url = f.get('authenticated_download_url')
        permissions = f.get('permissions') or {}
        if authenticated_download_url and f.get('is_download_available') and permissions.get('can_download', True):
            formats.append({
                'ext': f.get('extension') or determine_ext(title),
                'filesize': f.get('size'),
                'format_id': 'download',
                'url': update_url_query(authenticated_download_url, query),
            })

        self._sort_formats(formats)

        creator = f.get('created_by') or {}

        return {
            'id': file_id,
            'title': title,
            'formats': formats,
            'description': f.get('description') or None,
            'uploader': creator.get('name'),
            'timestamp': parse_iso8601(f.get('created_at')),
            'uploader_id': creator.get('id'),
        }
