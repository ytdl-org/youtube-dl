# coding: utf-8
from __future__ import unicode_literals

from .common import (
    InfoExtractor,
    ExtractorError,
)

from ..utils import (
    clean_html,
    str_or_none,
)

import re

# this infoextractor is for services implementing the Mastodon API, not just Mastodon
# supported services (possibly more already work or could):
# - Mastodon - https://github.com/tootsuite/mastodon
# - Glitch (a fork of Mastodon) - https://github.com/glitch-soc/mastodon
# - Pleroma - https://git.pleroma.social/pleroma/pleroma
# - Gab Social (a fork of Mastodon) - https://code.gab.com/gab/social/gab-social/


class MastodonIE(InfoExtractor):
    IE_NAME = 'mastodon'
    _VALID_URL = r'https?://(?P<host>[^/\s]+)(?<!facebook\.com)/(?:(?:@[a-zA-Z0-9_]+|[a-zA-Z0-9_]+/posts|users/[a-zA-Z0-9_]+/statuses)|notice|objects)/(?P<id>[0-9a-zA-Z-]+)'

    _TESTS = [{
        # mastodon, video description
        "url": "https://mastodon.technology/@BadAtNames/104254332187004304",
        "info_dict": {
            "id": "104254332187004304",
            "title": "BadAtNames - Mfw trump supporters complain about twitter",
            "ext": "mp4",
            "description": "md5:53f4428d4dc7e25a8255cf2a08488f2e",
        },
    }, {
        # pleroma, /objects/ redirect, empty content
        "url": "https://fedi.valkyrie.world/objects/386d2d68-090f-492e-81bd-8d32a3a65627",
        "info_dict": {
            "id": "9xLMO1BcEEbaM54LBI",
            "title": "VD-15 - ",
            "ext": "mp4",
            "description": "video0_4_1.mp4",
        },
    }, {
        # pleroma, multiple videos in single post (can't define tests for _type multi_video)
        "url": "https://donotsta.re/notice/9xN1v6yM7WhzE7aIIC",
        "only_matching": True,
    }, {
        # gab social
        "url": "https://gab.com/ACT1TV/posts/104450493441154721",
        "info_dict": {
            "id": "104450493441154721",
            "title": "Bill Blaze - He shoots, he scores and the crowd went wild.... #Animal #Sports",
            "ext": "mp4",
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host, id = mobj.group('host', 'id')

        if '/objects/' in url:
            page = self._download_webpage(url, '%s@%s' % (id, host), expected_status=302)
            real_url = self._og_search_property('url', page, default=None)
            if real_url:
                return {
                    "_type": "url",
                    "ie_key": "Mastodon",
                    "url": real_url,
                }

        metadata = self._download_json('https://%s/api/v1/statuses/%s' % (host, id), '%s@%s' % (id, host))

        if not metadata['media_attachments']:
            raise ExtractorError('No attached medias')

        medias = []
        for media in metadata['media_attachments']:
            if media['type'] == 'video':
                medias.append(media)

        title = '%s - %s' % (str_or_none(metadata['account']['display_name'] or metadata['account']['acct']), clean_html(str_or_none(metadata['content'])))

        if len(medias) == 0:
            raise ExtractorError('No audio/video attachments')
        elif len(medias) == 1:
            media = medias[0]
            return {
                "id": id,
                "title": title,
                "description": str_or_none(media['description']),
                "url": str_or_none(media['url']),
                "thumbnail": str_or_none(media['preview_url']),
            }
        else:
            entries = []
            for media in medias:
                entries.append({
                    "id": id,
                    "title": str_or_none(media['description']) or title,
                    "url": str_or_none(media['url']),
                    "thumbnail": str_or_none(media['preview_url']),
                })
            return {
                "_type": "multi_video",
                "id": id,
                "title": title,
                "entries": entries,
            }
