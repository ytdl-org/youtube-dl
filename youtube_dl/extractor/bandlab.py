# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    merge_dicts,
    T,
    traverse_obj,
    txt_or_none,
    url_or_none,
)


class BandlabIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bandlab\.com/post/(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'https://www.bandlab.com/post/f117c6d9-9b14-ef11-96f5-000d3a425266',
        'info_dict': {
            'id': 'f117c6d9-9b14-ef11-96f5-000d3a425266',
            'ext': 'm4a',
            'title': 'essentials',
            'artist': 'Nico Tranquility',
        },
    }]

    def _real_extract(self, url):
        track_id = self._match_id(url)
        config = self._download_json(
            'http://www.bandlab.com/api/v1.3/posts/%s' % track_id, track_id)
        track_url = traverse_obj(config, ('revision', 'mixdown', 'file', T(url_or_none)))
        if not track_url:
            raise ExtractorError(
                '[%s] No video formats found!' % (self.ie_key(), ),
                video_id=track_id, expected=True)
        title = traverse_obj(config, ('revision', 'song', 'name', T(txt_or_none)))

        return {
            'id': track_id,
            'title': title,
            'url': track_url,
            'artist': traverse_obj(config, ('creator', 'name', T(txt_or_none))),
        }


class BandlabAlbumOrPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bandlab\.com/[^/]+/(?P<kind>albums|collections)/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://www.bandlab.com/nicoeskasenuatrans/albums/a7f108ca-74d6-ee11-85f9-00224845a8e0',
        'playlist': [
            {
                "info_dict": {
                    "id": "d30b09de-2320-4fc3-a778-c2cb8a01baf7",
                    "title": "self made",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "2b08f655-7ae5-407c-afbb-f0d6f5dec4ed",
                    "title": "pride",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "03259a33-613a-4e2b-a784-0cf67e82886a",
                    "title": "free speech",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "5264bf91-9700-4603-9a78-c40d2aee2a56",
                    "title": "legalize insanity",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "a32c22f5-945c-4bb5-91d6-3419f96b92bf",
                    "title": "euphoria",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "df065a3c-a36d-4e6e-81a8-c2b94204b1c6",
                    "title": "true colours (more euphoria)",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "e0bf4b18-deb2-4a09-99e2-07d45bcc9c1e",
                    "title": "manifest",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "a6b0c087-8980-4699-954b-7ee0376be7f6",
                    "title": "survivor's guilt",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "19b80025-6557-43d5-85b9-cd9f6075f27e",
                    "title": "memories",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "ff6a0fdf-afb5-40d0-902f-1f1760b74c75",
                    "title": "it gets better",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "12e77b89-43e6-42ef-b1c9-f7551f108f16",
                    "title": "undeletable",
                    "ext": "m4a"
                }
            },
            {
                "info_dict": {
                    "id": "f2b959bf-4014-4c5d-8079-3f6d0b9ca5b9",
                    "title": "antifascientist",
                    "ext": "m4a"
                }
            }
        ],
        'info_dict': {
            'id': 'a7f108ca-74d6-ee11-85f9-00224845a8e0',
            'album': 'trans*',
            'artist': 'Nico Tranquility'
        },
    }, {
        'url': 'https://www.bandlab.com/hexatetrahedronx/collections/8fb1041c-e865-eb11-9889-0050f28a2802',
        'playlist': [
            {
                'info_dict': {
                    'id': '8f37e4aa-92c4-eb11-a7ad-0050f280467f',
                    'title': 'psych ward',
                    'ext': 'm4a'
                }
            }
        ],
        'info_dict': {
            'id': '8fb1041c-e865-eb11-9889-0050f28a2802',
            'album': 'DOOMTAPE',
            'artist': '12days'
        }
    }]

    def _real_extract(self, url):
        resource_id, kind = self._match_valid_url(url).group('id', 'kind')
        config = self._download_json(
            'http://www.bandlab.com/api/v1.3/%s/%s' % (kind, resource_id), resource_id)
        entries = []
        for track in traverse_obj(config, ('posts', Ellipsis)):
            url, name = (traverse_obj(track, ('track', {
                'url': ('sample', 'audioUrl', T(url_or_none)),
                'name': ('name', T(txt_or_none)),
            }), ('revision', {
                'url': ('mixdown', 'file', T(url_or_none)),
                'name': ('song', 'name', T(txt_or_none)),
            })).get(x) for x in ('url', 'name'))
            if not (url and name):
                continue
            track_id = self._search_regex(
                r'/([^/]+)\.m4a$', url, 'track id', default=None)
            if not track_id:
                continue
            entries.append({
                'url': url,
                'id': track_id,
                'title': name,
            })

        return merge_dicts(
            self.playlist_result(entries, playlist_id=resource_id),
            traverse_obj(config, {
                'album': ('name', T(txt_or_none)),
                'artist': ('creator', 'name', T(txt_or_none)),
            }))
