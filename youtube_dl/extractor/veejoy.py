# coding: utf-8
from __future__ import unicode_literals
import json

from .common import InfoExtractor


class VeejoyIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?veejoy.de\/[a-z]{2}\/((?:movies)|(?:series))\/(?P<id>[a-zA-z-/]+)'
    _TESTS = [{
        'url': 'https://www.veejoy.de/en/movies/on-ride-tyrol-log-flume',
        'info_dict': {
            'id': 'on-ride-tyrol-log-flume',
            'ext': 'mp4',
            'title': 'On-ride Tyrol Log Flume',
            'description': 'Through the ‘magical world of diamonds’ and straight into the cool water. Experience a different kind of water slide with the ‘Tyrol Log Flume’. One of the oldest and most popular attractions in the park!',
            'uploader': 'MACK Media'
        }
    }, {
        'url': 'https://www.veejoy.de/en/movies/off-to-rulantica',
        'info_dict': {
            'id': 'off-to-rulantica',
            'ext': 'mp4',
            'title': 'Off to Rulantica',
            'description': 'Rocking through the water on round boats, creating splashy fun with water cannons – and then, sliding down ‘Svalgurok’ on ten different slides: Soaking wet water fun is calling.',
            'uploader': 'Veejoy'
        }
    }, {
        'url': 'https://www.veejoy.de/de/series/o-the-construction-documentary/the-building-site-grows',
        'info_dict': {
            'id': 'o-the-construction-documentary/the-building-site-grows',
            'ext': 'mp4',
            'title': 'Bau-„Leiter“',
            'description': 'Auf der Baustelle ist viel passiert. Patrick und Lukas bekommen ein Update vom Bauleiter, erklären technische Grundlagen am „lebenden Objekt“ und stellen sich einer Onride-Challenge.',
            'uploader': 'MACK Media'
        }
    }]

    def get_video_id(self, url):
        return self._match_id(url)

    def get_video_data(self, url, video_id):
        webpage = self._download_webpage(url, video_id)
        next_data = self._html_search_regex(r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>', webpage, 'next_data')
        return json.loads(next_data)["props"]["pageProps"]["media"]

    def get_producer(self, video_data):
        if "item" in video_data["studioDetails"]:
            return video_data["studioDetails"]["item"]["title"]
        else:
            return "Veejoy"

    def get_thumbnails(self, video_data):
        thumbnails = []

        thumb_3_4 = video_data["teaserImage"]["3_4"]
        if thumb_3_4:
            thumbnails.append({
                'url': thumb_3_4["srcSet"][1].split(" ")[0],
            })

        thumb_16_9 = video_data["teaserImage"]["16_9"]
        if thumb_16_9:
            thumbnails.append({
                'url': thumb_16_9["srcSet"][1].split(" ")[0],
            })

        return thumbnails

    def get_asset_ref(self, video_data):
        for mediaAsset in video_data["mediaAssets"]:
            if mediaAsset["type"] == "SOURCE":
                return mediaAsset["assetReference"]

    def get_asset_formats(self, video_data, video_id):
        asset = self._download_json("https://www.veejoy.de/api/service/get-media-summary?mediaIri=" + self.get_asset_ref(video_data) + "&locale=en", video_id)
        return asset["assetFormats"]

    def get_original_file_url(self, video_data, video_id):
        for asset_format in self.get_asset_formats(video_data, video_id):
            if asset_format["mimeType"] == "video/mp4":
                return asset_format

    def get_video_formats(self, asset_formats):
        # This function is currently faulty and thus not used
        formats = []

        for asset_format in asset_formats:
            if asset_format["mimeType"] == "application/vnd.apple.mpegurl":
                formats.append({
                    'url': asset_format["contentUrl"],
                    'width': asset_format["transcodingFormat"]["videoWidth"],
                    'quality': asset_format["transcodingFormat"]["id"],
                    'language': asset_format["language"],
                })

        return formats

    def _real_extract(self, url):
        video_id = self.get_video_id(url)
        video_data = self.get_video_data(url, video_id)
        producer = self.get_producer(video_data)
        thumbnails = self.get_thumbnails(video_data)
        final_asset = self.get_original_file_url(video_data, video_id)

        return {
            'url': final_asset.get("contentUrl"),
            'id': video_id,
            'title': video_data.get("title"),
            'description': video_data.get("shortDescription"),
            'duration': video_data.get("mediaDuration"),
            'uploader': producer,
            'creator': producer,
            'thumbnails': thumbnails,
        }
