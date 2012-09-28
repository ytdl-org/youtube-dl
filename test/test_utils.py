# -*- coding: utf-8 -*-

# Various small unit tests

from youtube_dl.utils import sanitize_filename

def test_sanitize_filename():
	assert sanitize_filename(u'abc') == u'abc'
	assert sanitize_filename(u'abc_d-e') == u'abc_d-e'

	assert sanitize_filename(u'123') == u'123'

	assert u'/' not in sanitize_filename(u'abc/de')
	assert u'abc' in sanitize_filename(u'abc/de')
	assert u'de' in sanitize_filename(u'abc/de')
	assert u'/' not in sanitize_filename(u'abc/de///')

	assert u'\\' not in sanitize_filename(u'abc\\de')
	assert u'abc' in sanitize_filename(u'abc\\de')
	assert u'de' in sanitize_filename(u'abc\\de')

	assert sanitize_filename(u'ä') == u'ä'
	assert sanitize_filename(u'кириллица') == u'кириллица'
