from __future__ import unicode_literals

import errno
import json
import os
import re
import shutil
import traceback

from .compat import (
    compat_getenv,
    compat_open as open,
)
from .utils import (
    error_to_compat_str,
    expand_path,
    is_outdated_version,
    try_get,
    write_json_file,
)
from .version import __version__


class Cache(object):

    _YTDL_DIR = 'youtube-dl'
    _VERSION_KEY = _YTDL_DIR + '_version'
    _DEFAULT_VERSION = '2021.12.17'

    def __init__(self, ydl):
        self._ydl = ydl

    def _get_root_dir(self):
        res = self._ydl.params.get('cachedir')
        if res is None:
            cache_root = compat_getenv('XDG_CACHE_HOME', '~/.cache')
            res = os.path.join(cache_root, self._YTDL_DIR)
        return expand_path(res)

    def _get_cache_fn(self, section, key, dtype):
        assert re.match(r'^[a-zA-Z0-9_.-]+$', section), \
            'invalid section %r' % section
        assert re.match(r'^[a-zA-Z0-9_.-]+$', key), 'invalid key %r' % key
        return os.path.join(
            self._get_root_dir(), section, '%s.%s' % (key, dtype))

    @property
    def enabled(self):
        return self._ydl.params.get('cachedir') is not False

    def store(self, section, key, data, dtype='json'):
        assert dtype in ('json',)

        if not self.enabled:
            return

        fn = self._get_cache_fn(section, key, dtype)
        try:
            try:
                os.makedirs(os.path.dirname(fn))
            except OSError as ose:
                if ose.errno != errno.EEXIST:
                    raise
            write_json_file({self._VERSION_KEY: __version__, 'data': data}, fn)
        except Exception:
            tb = traceback.format_exc()
            self._ydl.report_warning(
                'Writing cache to %r failed: %s' % (fn, tb))

    def _validate(self, data, min_ver):
        version = try_get(data, lambda x: x[self._VERSION_KEY])
        if not version:  # Backward compatibility
            data, version = {'data': data}, self._DEFAULT_VERSION
        if not is_outdated_version(version, min_ver or '0', assume_new=False):
            return data['data']
        self._ydl.to_screen(
            'Discarding old cache from version {version} (needs {min_ver})'.format(**locals()))

    def load(self, section, key, dtype='json', default=None, min_ver=None):
        assert dtype in ('json',)

        if not self.enabled:
            return default

        cache_fn = self._get_cache_fn(section, key, dtype)
        try:
            try:
                with open(cache_fn, 'r', encoding='utf-8') as cachef:
                    return self._validate(json.load(cachef), min_ver)
            except ValueError:
                try:
                    file_size = os.path.getsize(cache_fn)
                except (OSError, IOError) as oe:
                    file_size = error_to_compat_str(oe)
                self._ydl.report_warning(
                    'Cache retrieval from %s failed (%s)' % (cache_fn, file_size))
        except IOError:
            pass  # No cache available

        return default

    def remove(self):
        if not self.enabled:
            self._ydl.to_screen('Cache is disabled (Did you combine --no-cache-dir and --rm-cache-dir?)')
            return

        cachedir = self._get_root_dir()
        if not any((term in cachedir) for term in ('cache', 'tmp')):
            raise Exception('Not removing directory %s - this does not look like a cache dir' % cachedir)

        self._ydl.to_screen(
            'Removing cache dir %s .' % cachedir, skip_eol=True)
        if os.path.exists(cachedir):
            self._ydl.to_screen('.', skip_eol=True)
            shutil.rmtree(cachedir)
        self._ydl.to_screen('.')
