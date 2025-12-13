# coding: utf-8
from __future__ import unicode_literals
import json

from .common import InfoExtractor
from ..utils import std_headers


class PlaySuisseIE(InfoExtractor):
    _MEDIA_URL = 'https://4bbepzm4ef.execute-api.eu-central-1.amazonaws.com/prod/graphql'
    _VALID_URL = r'https?://(?:www\.)?playsuisse\.ch/watch/(?P<id1>[0-9]+)'
    _TESTS = [
        {
            'url': 'https://www.playsuisse.ch/watch/763211/0',
            'md5': '0d716b7a16c3e6ab784ef817ee9a20c1',
            'info_dict': {
                'id': '763211',
                'ext': 'mp4',
                'title': 'Wilder S01E01 - Knochen',
                'description': 'md5:8ea7a8076ba000cd9e8bc132fd0afdd8'
            }
        },
        {
            'url': 'https://www.playsuisse.ch/watch/808675/0',
            'md5': '7aa043e69fea5044db2da8bb58bca239',
            'info_dict': {
                'id': '808675',
                'ext': 'mp4',
                'title': 'Der Läufer',
                'description': 'md5:'
            }
        },
        {
            'url': 'https://www.playsuisse.ch/watch/817913/0',
            'md5': '50721c46ca0b3a9836eb61ecb0ed7097',
            'info_dict': {
                'id': '42',
                'ext': 'mp4',
                'title': 'Nr. 47 S01E01 - Die Einweihungsparty',
                'description': 'md5:'
            }
        }
    ]

    def _get_media_data(self, media_id):
        locale = std_headers.get('locale', 'de').strip()
        # TODO find out why the locale has no effect in request
        response = self._download_json(
            self._MEDIA_URL,
            media_id,
            data=json.dumps({
                'operationName': 'AssetWatch',
                'query': self._GRAPHQL_QUERY,
                'variables': {
                    "assetId": media_id
                }
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'locale': locale})

        return response['data']['asset']

    def _real_extract(self, url):
        media_id, = self._VALID_URL_RE.match(url).groups()
        media_data = self._get_media_data(media_id)

        def _get_title(data):
            if data.get('seriesName'):
                return '{} S{:02}E{:02} - {}'.format(
                    data['seriesName'],
                    int(data['seasonNumber']),
                    int(data['episodeNumber']),
                    data['name'])
            else:
                return data['name']

        title = _get_title(media_data)
        description = media_data['description']
        thumbnails = [
            {
                'id': thumb['id'],
                'url': thumb['url']
            }
            for key, thumb in media_data.items()
            if key.startswith('thumbnail') and thumb is not None
        ]

        formats = []

        for media in media_data['medias']:
            # NOTE subtitle info is included in the m3u8 file, but it's not supported by ytdl
            # https://github.com/ytdl-org/youtube-dl/issues/6106
            if media['type'] == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    media['url'],
                    media_id,
                    'mp4',
                    'm3u8_native',
                    m3u8_id="HLS",
                    fatal=False))

            # NOTE seems to be 404 for all tested media
            elif media['type'] == 'DASH' and False:
                formats.extend(self._extract_mpd_formats(
                    media['url'],
                    media_id,
                    mpd_id='dash',
                    fatal=False
                ))

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'formats': formats,
        }

    _GRAPHQL_QUERY = '''\
query AssetWatch($assetId: ID!) {
  asset(assetId: $assetId) {
    ...Asset
    __typename
  }
}
fragment Asset on Asset {
  ...AssetDetails
  episodes {
    ...AssetDetails
    __typename
  }
  __typename
}
fragment AssetDetails on Asset {
  audioLanguages
  awards
  bu
  contentCategories
  contentCodes
  contentTypes
  contractType
  countries
  creators
  creditsTimeInSecs
  description
  descriptionLong
  directors
  downloadable
  duration
  editorialContentCategoriesDatalab {
    id
    title
    __typename
  }
  editorialContentMetaCategoriesDatalab {
    id
    title
    __typename
  }
  endDate
  episodeNumber
  episodesInSequence
  externalId
  firstEpisodeDuration
  id
  image16x9 {
    ...ImageDetails
    __typename
  }
  image2x3 {
    ...ImageDetails
    __typename
  }
  image16x9WithTitle {
    ...ImageDetails
    __typename
  }
  image2x3WithTitle {
    ...ImageDetails
    __typename
  }
  mainCast
  name
  nextEpisode {
    id
    episodeNumber
    seasonNumber
    numberOfEpisodesInSeason
    image16x9 {
      ...ImageDetails
      __typename
    }
    __typename
  }
  numberOfSeasons
  otherKeyPeople
  parentalRating
  popularity
  premium
  presenters
  primaryLanguage
  productionCompanies
  productionCountries
  provider
  ratings
  regions
  restrictions
  seasons {
    seasonNumber
    assetIds
    __typename
  }
  seasonNumber
  seriesId
  seriesName
  nextEpisode {
    ...NextEpisodeDetails
    __typename
  }
  parentId
  startDate
  subtitleLanguages
  tagline
  targetAudience
  themes
  thumbnail16x9 {
    ...ImageDetails
    __typename
  }
  thumbnail2x3 {
    ...ImageDetails
    __typename
  }
  thumbnail16x9WithTitle {
    ...ImageDetails
    __typename
  }
  thumbnail2x3WithTitle {
    ...ImageDetails
    __typename
  }
  type
  writers
  year
  medias {
    ...MediaDetails
    __typename
  }
  trailerMedias {
    ...MediaDetails
    __typename
  }
  sponsors {
    ...SponsorDetails
    __typename
  }
  sponsorEndDate
  __typename
}
fragment ImageDetails on Image {
  id
  url
  alt
  __typename
}
fragment MediaDetails on Media {
  id
  type
  url
  duration
  __typename
}
fragment SponsorDetails on Sponsor {
  id
  name
  description
  type
  externalId
  image16x9 {
    ...ImageDetails
    __typename
  }
  thumbnail16x9 {
    ...ImageDetails
    __typename
  }
  __typename
}
fragment NextEpisodeDetails on NextEpisode {
  id
  episodeNumber
  seasonNumber
  numberOfEpisodesInSeason
  image16x9 {
    ...ImageDetails
    __typename
  }
  __typename
}
'''
