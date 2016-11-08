# coding: utf-8
from __future__ import unicode_literals

import functools
import re

from .common import InfoExtractor
from ..utils import (
    OnDemandPagedList,
    determine_ext,
    parse_iso8601
)

class ZDFIE(InfoExtractor):
    _VALID_URL = r'https?://www\.zdf\.de/.*?/(?P<id>[^/?]*?)\.html'

    _TESTS = [{
        'url': 'https://www.zdf.de/service-und-hilfe/die-neue-zdf-mediathek/zdfmediathek-trailer-100.html',
        'info_dict': {
            'id': 'zdfmediathek-trailer-100',
            'ext': 'mp4',
            'title': 'Trailer ZDFmediathek Supermarkt',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        jsb = self._search_regex(r"data-zdfplayer-jsb='([^']*)'", webpage, 'zdfplayer jsb data')
        jsb_json = self._parse_json(jsb, video_id)

        configuration_url = 'https://www.zdf.de' + jsb_json['config']
        configuration_json = self._download_json(configuration_url, video_id, note='Downloading player configuration')
        api_token = configuration_json['apiToken']

        player_js = self._download_webpage('https://www.zdf.de/ZDFplayer/latest-v2/skins/zdf/zdf-player.js', video_id, fatal=False, note='Downloading player script')
        if player_js:
            player_id = self._search_regex(r'this\.ptmd_player_id="([^"]*)"', player_js, 'player id', fatal=False)
        else:
            player_id = None

        content_json = self._download_json(jsb_json['content'], video_id, headers={'Api-Auth': 'Bearer %s' % api_token}, note='Downloading content description')
        main_video_content = content_json['mainVideoContent']['http://zdf.de/rels/target']
        meta_data_url = None
        if not player_id:
            # could not determine player_id => try alternativ generic URL
            meta_data_url = main_video_content.get('http://zdf.de/rels/streams/ptmd')
            if meta_data_url:
                meta_data_url = 'https://api.zdf.de' + meta_data_url
            else:
                # no generic URL found => 2nd fallback: hardcoded player_id
                player_id = 'ngplayer_2_3'
        if not meta_data_url:
            meta_data_url_template = main_video_content['http://zdf.de/rels/streams/ptmd-template']
            meta_data_url = 'https://api.zdf.de' + meta_data_url_template.replace('{playerId}', player_id)

        title = content_json['title']

        meta_data = self._download_json(meta_data_url, video_id, note='Downloading meta data')

        formats = []
        for p_list_entry in meta_data['priorityList']:
            for formitaet in p_list_entry['formitaeten']:
                # mime = formitaet.get('mimeType')
                facets = formitaet.get('facets') or []
                add = ''
                if formitaet.get('isAdaptive'):
                    add += 'a'
                    facets.append('adaptive')
                if 'restriction_useragent' in facets:
                    add += 'b'
                if 'progressive' in facets:
                    add += 'p'
                type_ = formitaet['type']
                for entry in formitaet['qualities']:
                    tracks = entry['audio']['tracks']
                    if not tracks:
                        continue
                    if len(tracks) > 1:
                        self._downloader.report_warning('unexpected input: multiple tracks')
                    track = tracks[0]
                    video_url = track['uri']
                    format_id = type_ + '-'
                    if add:
                        format_id += add + '-'
                    # named qualities are not very useful for sorting the formats:
                    # a 'high' m3u8 entry can be better quality than a 'veryhigh' direct mp4 download
                    format_id += entry['quality']
                    ext = determine_ext(video_url, None)
                    if ext == 'meta':
                        continue
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', m3u8_id=format_id, fatal=False))
                    elif ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            video_url, video_id, f4m_id=format_id, fatal=False))
                    else:
                        formats.append({
                            'format_id': format_id,
                            'url': video_url,
                            'format_note': ', '.join(facets)
                        })
        self._sort_formats(formats)

        subtitles = {}
        if meta_data.get('captions'):
            subtitles['de'] = []
            for caption in meta_data['captions']:
                if caption.get('language') == 'deu':
                    subformat = {'url': caption.get('uri')}
                    if caption.get('format') == 'webvtt':
                        subformat['ext'] = 'vtt'
                    elif caption.get('format') == 'ebu-tt-d-basic-de':
                        subformat['ext'] = 'ttml'
                    subtitles['de'].append(subformat)

        teaser_images = content_json.get('teaserImageRef')
        if teaser_images:
            teaser_images_layouts = teaser_images.get('layouts')
            if teaser_images_layouts:
                thumbnail = teaser_images_layouts.get('original')
            else:
                thumbnail = None
        else:
            thumbnail = None

        description = content_json.get('teasertext')
        timestamp = parse_iso8601(content_json.get('editorialDate'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'description': description,
            'timestamp': timestamp
        }

class ZDFChannelIE(InfoExtractor):
    _WORKING = False
    _VALID_URL = r'(?:zdf:topic:|https?://www\.zdf\.de/ZDFmediathek(?:#)?/.*kanaluebersicht/(?:[^/]+/)?)(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.zdf.de/ZDFmediathek#/kanaluebersicht/1586442/sendung/Titanic',
        'info_dict': {
            'id': '1586442',
        },
        'playlist_count': 3,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/meist-gesehen/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/_/1798716?bc=nrt;nrm?flash=off',
        'only_matching': True,
    }]
    _PAGE_SIZE = 50

    def _fetch_page(self, channel_id, page):
        offset = page * self._PAGE_SIZE
        xml_url = (
            'http://www.zdf.de/ZDFmediathek/xmlservice/web/aktuellste?ak=web&offset=%d&maxLength=%d&id=%s'
            % (offset, self._PAGE_SIZE, channel_id))
        doc = self._download_xml(
            xml_url, channel_id,
            note='Downloading channel info',
            errnote='Failed to download channel info')

        title = doc.find('.//information/title').text
        description = doc.find('.//information/detail').text
        for asset in doc.findall('.//teasers/teaser'):
            a_type = asset.find('./type').text
            a_id = asset.find('./details/assetId').text
            if a_type not in ('video', 'topic'):
                continue
            yield {
                '_type': 'url',
                'playlist_title': title,
                'playlist_description': description,
                'url': 'zdf:%s:%s' % (a_type, a_id),
            }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        entries = OnDemandPagedList(
            functools.partial(self._fetch_page, channel_id), self._PAGE_SIZE)

        return {
            '_type': 'playlist',
            'id': channel_id,
            'entries': entries,
        }
