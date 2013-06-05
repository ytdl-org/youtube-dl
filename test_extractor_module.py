#!/usr/bin/env python
import youtube_dl.extractors as ex

print('Testing the new IEs module')
print(ex.gen_extractors())
print(ex.get_info_extractor('Test'))
ex.get_info_extractor('Test2').test()
