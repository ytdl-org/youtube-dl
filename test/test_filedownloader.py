import unittest

from test.helper import FakeYDL

from youtube_dl import FileDownloader


class BaseTestFileDownloader(unittest.TestCase):
    params = {}

    def setUp(self):
        self.downloader = FileDownloader(FakeYDL(), self.params)


class TestPartFileDefaults(BaseTestFileDownloader):
    params = {}

    def test_temp_name_missing_file(self):
        # file is missing: should add the default suffix
        fn = self.downloader.temp_name('some file.ext')
        self.assertEqual(fn, 'some file.ext.part')

    def test_undo_temp_name_no_suffix(self):
        # file doesn't end with the suffix: should be untouched
        fn = self.downloader.undo_temp_name('some file.ext')
        self.assertEqual(fn, 'some file.ext')

    def test_undo_temp_name_with_suffix(self):
        # file ends with the suffix: should be removed
        fn = self.downloader.undo_temp_name('some file.ext.part')
        self.assertEqual(fn, 'some file.ext')


class TestPartFileCustomSuffix(BaseTestFileDownloader):
    params = {'partsuffix': '.othersuffix'}

    def test_temp_name_missing_file(self):
        # file is missing: should add the custom suffix
        fn = self.downloader.temp_name('some file.ext')
        self.assertEqual(fn, 'some file.ext.othersuffix')

    def test_undo_temp_name_no_suffix(self):
        # file doesn't end with the suffix: should be untouched
        fn = self.downloader.undo_temp_name('some file.ext')
        self.assertEqual(fn, 'some file.ext')

    def test_undo_temp_name_default_suffix(self):
        # file ends with the default suffix: should be untouched
        fn = self.downloader.undo_temp_name('some file.ext.part')
        self.assertEqual(fn, 'some file.ext.part')

    def test_undo_temp_name_custom_suffix(self):
        # file ends with the custom suffix: should be removed
        fn = self.downloader.undo_temp_name('some file.ext.othersuffix')
        self.assertEqual(fn, 'some file.ext')


if __name__ == '__main__':
    unittest.main()
