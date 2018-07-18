# coding: utf-8
from __future__ import unicode_literals

from .theplatform import ThePlatformFeedIE


class MediasetIE(ThePlatformFeedIE):
    _VALID_URL = r'''(?x)
                    (?:
                        mediaset:|
                        https?://
                            (?:www\.)?mediasetplay\.mediaset\.it/video/
                                (?:[^/]+/)
                                (?:[^/_]+)_
                    )(?P<id>F[0-9]+)
                    '''
    _TESTS = [{
        # full episode
        'url': 'https://www.mediasetplay.mediaset.it/video/temptationisland/lunedi-16-luglio-seconda-puntata_F309179001000201',
        'md5': 'aea24e52e32bf3e1dae8e0c54c7a1370',
        'info_dict': {
            'id': 'F309179001000201',
            'ext': 'mpd',
            'title': 'Lunedì 16 luglio - Seconda puntata',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 10045.01,
            'upload_date': '20180717',
            'uploader': 'FINC-MSIT',
            'timestamp': 1531789469,
        }
    }, {
        'url': 'https://www.mediasetplay.mediaset.it/video/beforewego/before-we-go_F307046901000103',
        'md5': '50eba7a60b5142ae232a1d9858d84e57',
        'info_dict': {
            'id': 'F307046901000103',
            'ext': 'mpd',
            'title': 'Before we go',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 5478.014,
            'upload_date': '20180714',
            'uploader': 'FINC-MSIT',
            'timestamp': 1531529416,
        }
    }]

    def _download_theplatform_metadata(self, path, video_id):
        info_url = 'http://link.theplatform.eu/s/%s?format=preview' % path
        return self._download_json(info_url, video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        provider_id = 'PR1GhC'
        real_url = 'https://feed.entertainment.tv.theplatform.eu/f/%s/mediaset-prod-all-programs?byGuid=%s' % (provider_id, video_id)
        entry = self._download_json(real_url, video_id)['entries'][0]

        theplatform_id = entry['media'][0]['pid']
        smil_url = 'https://link.theplatform.eu/s/%s/media/%s?format=smil' % (provider_id, theplatform_id)
        formats, subtitles = self._extract_theplatform_smil(smil_url, video_id)

        path = provider_id + '/media/' + theplatform_id
        ret = self._extract_theplatform_metadata(path, video_id)
        ret.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        })

        return ret
