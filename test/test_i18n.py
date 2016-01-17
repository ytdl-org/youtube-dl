#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import contextlib
import os
import shutil
import subprocess
import sys

try:
    import unittest
    unittest.TestCase.setUpClass
except AttributeError:
    import unittest2 as unittest

# Allow direct execution
rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootDir)

from youtube_dl.version import __version__
from youtube_dl.compat import subprocess_check_output
from youtube_dl.utils import decodeFilename

rootDir_u = decodeFilename(rootDir)


@contextlib.contextmanager
def chdir_to(path):
    oldpwd = os.getcwd()
    os.chdir(os.path.join(rootDir_u, path))
    yield
    os.chdir(oldpwd)


class I18NTestCase(object):
    @classmethod
    def setUpClass(cls):
        with chdir_to('.'):
            cls.make('update-gmo')

        cls.install()

        # avoid false positive
        with chdir_to('.'):
            shutil.rmtree(os.path.join('share', 'locale'))

    @classmethod
    def tearDownClass(cls):
        cls.uninstall()

    @classmethod
    def make(cls, target):
        with chdir_to('.'):
            subprocess.check_call([
                'make', target], env=dict(os.environ, PYTHON=sys.executable))

    def test_lang_opt(self):
        def output_with_lang_opt(lang):
            return subprocess_check_output([
                sys.executable, self.PROGRAM, 'i18n:test', '--lang', lang
            ]).decode('utf-8').strip()

        self.assertEqual(output_with_lang_opt('en_US.UTF-8'), 'I18N test message')
        self.assertEqual(output_with_lang_opt('zh_TW.UTF-8'), 'I18N測試訊息')

    def test_lc_all(self):
        def output_with_lc_all(lang):
            return subprocess_check_output([
                sys.executable, self.PROGRAM, 'i18n:test'
            ], env=dict(os.environ, LC_ALL=lang)).decode('utf-8').strip()

        self.assertEqual(output_with_lc_all('en_US.UTF-8'), 'I18N test message')
        self.assertEqual(output_with_lc_all('zh_TW.UTF-8'), 'I18N測試訊息')


@unittest.skipUnless(os.environ.get('VIRTUAL_ENV'), 'Requires virtualenv because of call to pip install')
class TestPipInstall(I18NTestCase, unittest.TestCase):
    @classmethod
    def install(cls):
        cls.PROGRAM = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'youtube-dl')

        with chdir_to('.'):
            subprocess.check_call([sys.executable, 'setup.py', '--quiet', 'sdist'])

        with chdir_to('test'):
            subprocess.check_call([
                'pip', 'install', '--quiet',
                os.path.join('..', 'dist', 'youtube_dl-%s.tar.gz' % __version__)])

    @classmethod
    def uninstall(cls):
        with chdir_to('test'):
            subprocess.check_call(['pip', 'uninstall', '--yes', 'youtube_dl'])


@unittest.skipUnless(os.environ.get('VIRTUAL_ENV'), 'Requires virtualenv because of call to setup.py install')
class TestDirectInstall(I18NTestCase, unittest.TestCase):
    @classmethod
    def install(cls):
        cls.PROGRAM = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'youtube-dl')

        with chdir_to('.'):
            subprocess.check_call([sys.executable, 'setup.py', '--quiet', 'install'])

    @classmethod
    def uninstall(cls):
        with chdir_to('test'):
            subprocess.check_call(['pip', 'uninstall', '--yes', 'youtube_dl'])


class TestZippedApp(I18NTestCase, unittest.TestCase):
    PROGRAM = os.path.join(rootDir_u, 'youtube-dl')

    @classmethod
    def install(cls):
        with chdir_to('.'):
            cls.make('youtube-dl')

    @classmethod
    def uninstall(cls):
        with chdir_to('.'):
            os.unlink('youtube-dl')

if __name__ == '__main__':
    unittest.main()
