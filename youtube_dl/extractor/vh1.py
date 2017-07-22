from __future__ import unicode_literals

from .mtv import MTVIE

import re
from ..utils import fix_xml_ampersands


class VH1IE(MTVIE):
    IE_NAME = 'vh1.com'
    _FEED_URL = 'http://www.vh1.com/player/embed/AS3/fullepisode/rss/'
    _TESTS = [{
        'url': 'http://www.vh1.com/video/metal-evolution/full-episodes/progressive-metal/1678612/playlist.jhtml',
        'playlist': [
            {
                'md5': '7827a7505f59633983165bbd2c119b52',
                'info_dict': {
                    'id': '731565',
                    'ext': 'mp4',
                    'title': 'Metal Evolution: Ep. 11 Act 1',
                    'description': 'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 12 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                }
            },
            {
                'md5': '34fb4b7321c546b54deda2102a61821f',
                'info_dict': {
                    'id': '731567',
                    'ext': 'mp4',
                    'title': 'Metal Evolution: Ep. 11 Act 2',
                    'description': 'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                }
            },
            {
                'md5': '813f38dba4c1b8647196135ebbf7e048',
                'info_dict': {
                    'id': '731568',
                    'ext': 'mp4',
                    'title': 'Metal Evolution: Ep. 11 Act 3',
                    'description': 'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                }
            },
            {
                'md5': '51adb72439dfaed11c799115d76e497f',
                'info_dict': {
                    'id': '731569',
                    'ext': 'mp4',
                    'title': 'Metal Evolution: Ep. 11 Act 4',
                    'description': 'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                }
            },
            {
                'md5': '93d554aaf79320703b73a95288c76a6e',
                'info_dict': {
                    'id': '731570',
                    'ext': 'mp4',
                    'title': 'Metal Evolution: Ep. 11 Act 5',
                    'description': 'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                }
            }
        ],
        'skip': 'Blocked outside the US',
    }, {
        # Clip
        'url': 'http://www.vh1.com/video/misc/706675/metal-evolution-episode-1-pre-metal-show-clip.jhtml#id=1674118',
        'md5': '7d67cf6d9cdc6b4f3d3ac97a55403844',
        'info_dict': {
            'id': '706675',
            'ext': 'mp4',
            'title': 'Metal Evolution: Episode 1 Pre-Metal Show Clip',
            'description': 'The greatest documentary ever made about Heavy Metal begins as our host Sam Dunn travels the globe to seek out the origins and influences that helped create Heavy Metal. Sam speaks to legends like Kirk Hammett, Alice Cooper, Slash, Bill Ward, Geezer Butler, Tom Morello, Ace Frehley, Lemmy Kilmister, Dave Davies, and many many more. This episode is the prologue for the 11 hour series, and Sam goes back to the very beginning to reveal how Heavy Metal was created.'
        },
        'skip': 'Blocked outside the US',
    }, {
        # Short link
        'url': 'http://www.vh1.com/video/play.jhtml?id=1678353',
        'md5': '853192b87ad978732b67dd8e549b266a',
        'info_dict': {
            'id': '730355',
            'ext': 'mp4',
            'title': 'Metal Evolution: Episode 11 Progressive Metal Sneak',
            'description': 'In Metal Evolution\'s finale sneak, Sam sits with Michael Giles of King Crimson and gets feedback from Metallica guitarist Kirk Hammett on why the group was influential.'
        },
        'skip': 'Blocked outside the US',
    }, {
        'url': 'http://www.vh1.com/video/macklemore-ryan-lewis/900535/cant-hold-us-ft-ray-dalton.jhtml',
        'md5': 'b1bcb5b4380c9d7f544065589432dee7',
        'info_dict': {
            'id': '900535',
            'ext': 'mp4',
            'title': 'Macklemore & Ryan Lewis - "Can\'t Hold Us ft. Ray Dalton"',
            'description': 'The Heist'
        },
        'skip': 'Blocked outside the US',
    }]

    _VALID_URL = r'''(?x)
        https?://www\.vh1\.com/video/
        (?:
            .+?/full-episodes/.+?/(?P<playlist_id>[^/]+)/playlist\.jhtml
        |
            (?:
            play.jhtml\?id=|
            misc/.+?/.+?\.jhtml\#id=
            )
            (?P<video_id>[0-9]+)$
        |
            [^/]+/(?P<music_id>[0-9]+)/[^/]+?
        )
    '''

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj.group('music_id'):
            id_field = 'vid'
            video_id = mobj.group('music_id')
        else:
            video_id = mobj.group('playlist_id') or mobj.group('video_id')
            id_field = 'id'
        doc_url = '%s?%s=%s' % (self._FEED_URL, id_field, video_id)

        idoc = self._download_xml(
            doc_url, video_id,
            'Downloading info', transform_source=fix_xml_ampersands)

        entries = []
        for item in idoc.findall('.//item'):
            info = self._get_video_info(item)
            if info:
                entries.append(info)

        return self.playlist_result(entries, playlist_id=video_id)
