#!/usr/bin/env python2
import hashlib
import os
import json
import unittest
import sys

from youtube_dl.FileDownloader import FileDownloader
#import all the info extractor
import youtube_dl

DEF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests.json')
PARAM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parameters.json'
)


class TestDownload(unittest.TestCase):
    pass


def md5_for_file(filename, block_size=2**20):
    with open(filename) as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def generator(name, url, md5, file, ie_param, optional_ie):
    def test_template(self):
        fd = FileDownloader(ie_param)
        fd.add_info_extractor(getattr(youtube_dl, name + "IE")())
        fd.download([url])
        self.assertTrue(os.path.exists(file))
        self.assertEqual(md5_for_file(file), md5)
    return test_template
    #only python 2.7

def clean_generator(files):
    def clean_template(self):
        for file_name in files:
            if os.path.exists(file_name):
                os.remove(file_name)
    return clean_template

with open(DEF_FILE, "r") as f:
    with open(PARAM_FILE) as fp:
        p = json.load(fp)
        test_param = json.load(f)
        files = set()
        for test_case in test_param:
            if test_case.get("broken", False):
                continue
            try:
                files.add(test_case["file"])
                test_method = generator(test_case['name'], test_case['url'], test_case['md5'], test_case['file'], p, test_case.get('add_ie', []))
                test_method.__name__ = "test_{0}".format(test_case["name"])
                setattr(TestDownload, test_method.__name__, test_method)
                del test_method
            except KeyError as e:
                sys.stderr.write("Issue with the parameters of test {0}.\n".format(test_case.get("name", "unknown test")))
        #clean the files
        ff = clean_generator(files)
        ff.__name__ = "tearDown"
        setattr(TestDownload, ff.__name__, ff)
        del ff


if __name__ == '__main__':
    unittest.main()
