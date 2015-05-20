# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DramaFeverIE(InfoExtractor):
    IE_NAME = 'dramafever'
    _VALID_URL = r'^https?://(?:www\.)?dramafever\.com/drama/(?P<id>[0-9]+/[0-9]+)/'
    _TESTS = [{
        'url': 'http://www.dramafever.com/drama/4512/1/Cooking_with_Shin/',
        'info_dict': {
            'id': '4512.1',
            'ext': 'flv',
            'title': 'Cooking with Shin 4512.1',
            'upload_date': '20140702',
            'description': 'Served at all special occasions and featured in the hit drama Heirs, Shin cooks Red Bean Rice.',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).replace("/", ".")

        consumer_secret = self._get_consumer_secret(video_id)

        ep_json = self._download_json(
            "http://www.dramafever.com/amp/episode/feed.json?guid=%s" % video_id,
            video_id, note='Downloading episode metadata',
            errnote="Video may not be available for your location")["channel"]["item"]

        title = ep_json["media-group"]["media-title"]
        description = ep_json["media-group"]["media-description"]
        thumbnail = ep_json["media-group"]["media-thumbnail"]["@attributes"]["url"]
        duration = int(ep_json["media-group"]["media-content"][0]["@attributes"]["duration"])
        mobj = re.match(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", ep_json["pubDate"])
        upload_date = mobj.group(1) + mobj.group(2) + mobj.group(3) if mobj is not None else None

        formats = []
        for vid_format in ep_json["media-group"]["media-content"]:
            src = vid_format["@attributes"]["url"]
            if '.f4m' in src:
                formats.extend(self._extract_f4m_formats(src, video_id))

        self._sort_formats(formats)
        video_subtitles = self.extract_subtitles(video_id, consumer_secret)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
            'subtitles': video_subtitles,
        }

    def _get_consumer_secret(self, video_id):
        df_js = self._download_webpage(
            "http://www.dramafever.com/static/126960d/v2/js/plugins/jquery.threadedcomments.js", video_id)
        return self._search_regex(r"'cs': '([0-9a-zA-Z]+)'", df_js, "cs")

    def _get_episodes(self, series_id, consumer_secret, episode_filter=None):
        _PAGE_SIZE = 60

        curr_page = 1
        max_pages = curr_page + 1
        results = []
        while max_pages >= curr_page:
            page_url = "http://www.dramafever.com/api/4/episode/series/?cs=%s&series_id=%s&page_size=%d&page_number=%d" % \
                       (consumer_secret, series_id, _PAGE_SIZE, curr_page)
            series = self._download_json(
                page_url, series_id, note="Downloading series json page #%d" % curr_page)
            max_pages = series['num_pages']
            results.extend([ep for ep in series['value'] if episode_filter is None or episode_filter(ep)])
            curr_page += 1
        return results

    def _get_subtitles(self, video_id, consumer_secret):

        def match_episode(ep):
            return ep['guid'] == video_id

        res = None
        info = self._get_episodes(
            video_id.split(".")[0], consumer_secret, episode_filter=match_episode)
        if len(info) == 1 and info[0]['subfile'] != '':
            res = {'en': [{'url': info[0]['subfile'], 'ext': 'srt'}]}
        return res


class DramaFeverSeriesIE(DramaFeverIE):
    IE_NAME = 'dramafever:series'
    _VALID_URL = r'^https?://(?:www\.)?dramafever\.com/drama/(?P<id>[0-9]+)/\d*[a-zA-Z_][a-zA-Z0-9_]*/'
    _TESTS = [{
        'url': 'http://www.dramafever.com/drama/4512/Cooking_with_Shin/',
        'info_dict': {
            'id': '4512',
            'title': 'Cooking with Shin',
            'description': 'Professional chef and cooking instructor Shin Kim takes some of the delicious dishes featured in your favorite dramas and shows you how to make them right at home.',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://www.dramafever.com/drama/124/IRIS/',
        'info_dict': {
            'id': '124',
            'title': 'IRIS',
            'description': 'Lee Byung Hun and Kim Tae Hee star in this powerhouse drama and ratings megahit of action, intrigue and romance.',
        },
        'playlist_count': 20,
    }]

    def _real_extract(self, url):
        series_id = self._match_id(url)
        consumer_secret = self._get_consumer_secret(series_id)

        series_json = self._download_json(
            "http://www.dramafever.com/api/4/series/query/?cs=%s&series_id=%s" % (consumer_secret, series_id),
            series_id, note='Downloading series metadata')["series"][series_id]

        title = series_json["name"]
        description = series_json["description_short"]

        episodes = self._get_episodes(series_id, consumer_secret)
        entries = []
        for ep in episodes:
            entries.append(self.url_result(
                'http://www.dramafever.com%s' % ep['episode_url'], 'DramaFever', ep['guid']))
        return self.playlist_result(entries, series_id, title, description)
