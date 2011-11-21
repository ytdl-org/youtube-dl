# -*- coding: utf-8 -*-

# Various small unit tests

import os,sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import youtube_dl

def test_simplify_title():
	assert youtube_dl._simplify_title(u'abc') == u'abc'
	assert youtube_dl._simplify_title(u'abc_d-e') == u'abc_d-e'

	assert youtube_dl._simplify_title(u'123') == u'123'

	assert u'/' not in youtube_dl._simplify_title(u'abc/de')
	assert u'abc' in youtube_dl._simplify_title(u'abc/de')
	assert u'de' in youtube_dl._simplify_title(u'abc/de')
	assert u'/' not in youtube_dl._simplify_title(u'abc/de///')

	assert u'\\' not in youtube_dl._simplify_title(u'abc\\de')
	assert u'abc' in youtube_dl._simplify_title(u'abc\\de')
	assert u'de' in youtube_dl._simplify_title(u'abc\\de')

	assert youtube_dl._simplify_title(u'ä') == u'ä'
	assert youtube_dl._simplify_title(u'кириллица') == u'кириллица'

	# Strip underlines
	assert youtube_dl._simplify_title(u'\'a_') == u'a'
