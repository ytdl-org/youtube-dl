# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import shutil
import tempfile

from youtube_dl import options
from youtube_dl.options import _hide_login_info


class TestOptions(unittest.TestCase):
    def test_hide_login_info(self):
        self.assertEqual(_hide_login_info(['-u', 'foo', '-p', 'bar']),
                         ['-u', 'PRIVATE', '-p', 'PRIVATE'])
        self.assertEqual(_hide_login_info(['-u']), ['-u'])
        self.assertEqual(_hide_login_info(['-u', 'foo', '-u', 'bar']),
                         ['-u', 'PRIVATE', '-u', 'PRIVATE'])
        self.assertEqual(_hide_login_info(['--username=foo']),
                         ['--username=PRIVATE'])


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'youtube-dl.conf')
        with io.open(self.config_file, 'w', encoding='utf-8') as config:
            config.write('--user-agent custom')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _parse_options(self, args, system_config='', user_config=''):
        old_argv, old_open = sys.argv, options.open

        def fake_open(filename, **kwargs):
            if filename == self.config_file:
                return old_open(filename, **kwargs)
            return io.StringIO(
                system_config if filename == '/etc/youtube-dl.conf' else user_config)

        sys.argv = ['youtube-dl'] + args
        options.open = fake_open
        try:
            return options.parseOpts()[1]
        finally:
            sys.argv, options.open = old_argv, old_open

    def test_config_defaults(self):
        opts = self._parse_options([])
        self.assertEqual(opts.config_location, None)
        self.assertFalse(opts.ignore_config)
        self.assertEqual(self._parse_options(
            [], '--user-agent system', '--user-agent user').user_agent, 'user')

    def test_config_location(self):
        for args in (
                ['--config-location', self.config_file],
                ['--config-location=' + self.config_file],
                ['--config-loc', self.config_file],
                ['--config-loc=' + self.config_file]):
            self.assertEqual(self._parse_options(
                args, '--user-agent system', '--user-agent user').user_agent, 'custom')

    def test_config_location_directory(self):
        for args in (
                ['--config-location', self.test_dir],
                ['--config-location=' + self.test_dir]):
            self.assertEqual(self._parse_options(args).user_agent, 'custom')

    def test_config_location_missing(self):
        missing = os.path.join(self.test_dir, 'missing.conf')
        for args in (
                ['--config-location', missing],
                ['--config-location=' + missing]):
            self.assertRaises(SystemExit, self._parse_options, args)

    def test_ignore_config(self):
        for flag in ('--ignore-config', '--ignore-conf'):
            opts = self._parse_options(
                [flag], '--user-agent system', '--user-agent user')
            self.assertTrue(opts.ignore_config)
            self.assertEqual(opts.user_agent, None)

    def test_config_location_with_ignore_config(self):
        for args in (
                ['--ignore-config', '--config-location', self.config_file],
                ['--config-location=' + self.config_file, '--ignore-config']):
            self.assertEqual(self._parse_options(
                args, '--user-agent system', '--user-agent user').user_agent, 'custom')

    def test_command_line_overrides_config(self):
        self.assertEqual(self._parse_options([
            '--config-location=' + self.config_file,
            '--user-agent', 'command-line']).user_agent, 'command-line')


if __name__ == '__main__':
    unittest.main()
