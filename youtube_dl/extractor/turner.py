# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    int_or_none,
    determine_ext,
    parse_duration,
    xpath_attr,
    update_url_query,
)


class TurnerBaseIE(InfoExtractor):
    def _extract_cvp_info(self, data_src, video_id, path_data={}):
        video_data = self._download_xml(data_src, video_id)
        video_id = video_data.attrib['id'].split('/')[-1].split('.')[0]
        title = xpath_text(video_data, 'headline', fatal=True)
        # rtmp_src = xpath_text(video_data, 'akamai/src')
        # if rtmp_src:
        #     splited_rtmp_src = rtmp_src.split(',')
        #     if len(splited_rtmp_src) == 2:
        #         rtmp_src = splited_rtmp_src[1]
        # aifp = xpath_text(video_data, 'akamai/aifp', default='')

        tokens = {}
        urls = []
        formats = []
        rex = re.compile(r'''(?x)
            (?P<width>[0-9]+)x(?P<height>[0-9]+)
            (?:_(?P<bitrate>[0-9]+))?
        ''')
        for video_file in video_data.findall('files/file'):
            video_url = video_file.text.strip()
            if not video_url:
                continue
            ext = determine_ext(video_url)
            if video_url.startswith('/mp4:protected/'):
                continue
                # TODO Correct extraction for these files
                # protected_path_data = path_data.get('protected')
                # if not protected_path_data or not rtmp_src:
                #     continue
                # protected_path = self._search_regex(
                #     r'/mp4:(.+)\.[a-z0-9]', video_url, 'secure path')
                # auth = self._download_webpage(
                #     protected_path_data['tokenizer_src'], query={
                #         'path': protected_path,
                #         'videoId': video_id,
                #         'aifp': aifp,
                #     })
                # token = xpath_text(auth, 'token')
                # if not token:
                #     continue
                # video_url = rtmp_src + video_url + '?' + token
            elif video_url.startswith('/secure/'):
                secure_path_data = path_data.get('secure')
                if not secure_path_data:
                    continue
                video_url = secure_path_data['media_src'] + video_url
                secure_path = self._search_regex(r'https?://[^/]+(.+/)', video_url, 'secure path') + '*'
                token = tokens.get(secure_path)
                if not token:
                    auth = self._download_xml(
                        secure_path_data['tokenizer_src'], video_id, query={
                            'path': secure_path,
                            'videoId': video_id,
                        })
                    token = xpath_text(auth, 'token')
                    if not token:
                        continue
                    tokens[secure_path] = token
                video_url = video_url + '?hdnea=' + token
            elif not re.match('https?://', video_url):
                base_path_data = path_data.get(ext, path_data.get('default', {}))
                media_src = base_path_data.get('media_src')
                if not media_src:
                    continue
                video_url = media_src + video_url
            if video_url in urls:
                continue
            urls.append(video_url)
            format_id = video_file.attrib['bitrate']
            if ext == 'smil':
                formats.extend(self._extract_smil_formats(video_url, video_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    update_url_query(video_url, {'hdcore': '3.7.0'}),
                    video_id, f4m_id=format_id, fatal=False))
            else:
                f = {
                    'format_id': format_id,
                    'url': video_url,
                    'ext': ext,
                }
                mobj = rex.search(format_id + video_url)
                if mobj:
                    f.update({
                        'width': int(mobj.group('width')),
                        'height': int(mobj.group('height')),
                        'tbr': int_or_none(mobj.group('bitrate')),
                    })
                elif format_id.isdigit():
                    f['tbr'] = int(format_id)
                else:
                    mobj = re.match(r'ios_(audio|[0-9]+)$', format_id)
                    if mobj:
                        if mobj.group(1) == 'audio':
                            f.update({
                                'vcodec': 'none',
                                'ext': 'm4a',
                            })
                        else:
                            f['tbr'] = int(mobj.group(1))
                formats.append(f)
        self._sort_formats(formats)

        subtitles = {}
        for source in video_data.findall('closedCaptions/source'):
            for track in source.findall('track'):
                source_url = source.get('url')
                if not source_url:
                    continue
                subtitles.set_default(source.get('lang') or source.get('label') or 'en', []).append({
                    'url': source_url,
                    'ext': {
                        'scc': 'scc',
                        'webvtt': 'vtt',
                        'smptett': 'tt',
                    }.get(source.get('format'))
                })

        thumbnails = [{
            'id': image.get('cut'),
            'url': image.text,
            'width': int_or_none(image.get('width')),
            'height': int_or_none(image.get('height')),
        } for image in video_data.findall('images/image')]

        timestamp = None
        if 'cnn.com' not in data_src:
            timestamp = int_or_none(xpath_attr(video_data, 'dateCreated', 'uts'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'description': xpath_text(video_data, 'description'),
            'duration': parse_duration(xpath_text(video_data, 'length') or xpath_text(video_data, 'trt')),
            'timestamp': timestamp,
            'upload_date': xpath_attr(video_data, 'metas', 'version'),
            'series': xpath_text(video_data, 'showTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
        }
