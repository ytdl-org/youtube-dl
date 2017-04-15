# coding: utf-8
from __future__ import unicode_literals

import os
import re
import subprocess
import tempfile

from .common import InfoExtractor
from ..utils import (
    check_executable,
    determine_ext,
    encodeArgument,
    ExtractorError,
)


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:openload\.(?:co|io)|oload\.tv)/(?:f|embed)/(?P<id>[a-zA-Z0-9-_]+)'

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/rjC09fkPLYs',
        'info_dict': {
            'id': 'rjC09fkPLYs',
            'ext': 'mp4',
            'title': 'movie.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': {
                'en': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,  # test subtitles only
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        'url': 'https://openload.co/f/_-ztPaZtMhM/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }, {
        'url': 'https://oload.tv/embed/KnG-kKZdcfY/',
        'only_matching': True,
    }]

    _PHANTOMJS_SCRIPT = r'''
        phantom.onError = function(msg, trace) {
          var msgStack = ['PHANTOM ERROR: ' + msg];
          if(trace && trace.length) {
            msgStack.push('TRACE:');
            trace.forEach(function(t) {
              msgStack.push(' -> ' + (t.file || t.sourceURL) + ': ' + t.line
                + (t.function ? ' (in function ' + t.function +')' : ''));
            });
          }
          console.error(msgStack.join('\n'));
          phantom.exit(1);
        };
        var page = require('webpage').create();
        page.settings.resourceTimeout = 10000;
        page.onInitialized = function() {
          page.evaluate(function() {
            delete window._phantom;
            delete window.callPhantom;
          });
        };
        page.open('https://openload.co/embed/%s/', function(status) {
          var info = page.evaluate(function() {
            return {
              decoded_id: document.getElementById('streamurl').innerHTML,
              title: document.querySelector('meta[name="og:title"],'
                + 'meta[name=description]').content
            };
          });
          console.log(info.decoded_id + ' ' + info.title);
          phantom.exit();
        });'''

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\']((?:https?://)?(?:openload\.(?:co|io)|oload\.tv)/embed/[a-zA-Z0-9-_]+)',
            webpage)

    def _real_extract(self, url):
        exe = check_executable('phantomjs', ['-v'])
        if not exe:
            raise ExtractorError('PhantomJS executable not found in PATH, '
                                 'download it from http://phantomjs.org',
                                 expected=True)

        video_id = self._match_id(url)
        url = 'https://openload.co/embed/%s/' % video_id
        webpage = self._download_webpage(url, video_id)

        if 'File not found' in webpage or 'deleted by the owner' in webpage:
            raise ExtractorError('File not found', expected=True, video_id=video_id)

        script_file = tempfile.NamedTemporaryFile(mode='w', delete=False)

        # write JS script to file and close it
        with script_file:
            script_file.write(self._PHANTOMJS_SCRIPT % video_id)

        self.to_screen('%s: Decoding video ID with PhantomJS' % video_id)

        p = subprocess.Popen([exe, '--ssl-protocol=any', script_file.name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        if p.returncode != 0:
            raise ExtractorError('Decoding failed\n:'
                                 + encodeArgument(err))
        else:
            decoded_id, title = encodeArgument(output).strip().split(' ', 1)

        os.remove(script_file.name)

        video_url = 'https://openload.co/stream/%s?mime=true' % decoded_id

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        entry = entries[0] if entries else {}
        subtitles = entry.get('subtitles')

        info_dict = {
            'id': video_id,
            'title': title,
            'thumbnail': entry.get('thumbnail') or self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            # Seems all videos have extensions in their titles
            'ext': determine_ext(title, 'mp4'),
            'subtitles': subtitles,
        }
        return info_dict
