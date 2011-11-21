# -*- coding: utf-8 -*-

# Various small unit tests

import os,sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import youtube_dl

def test_simplify_title():
	assert youtube_dl._simplify_title('abc') == 'abc'
	assert youtube_dl._simplify_title('abc_d-e') == 'abc_d-e'

	assert '/' not in youtube_dl._simplify_title('abc/de')
	assert 'abc' in youtube_dl._simplify_title('abc/de')
	assert 'de' in youtube_dl._simplify_title('abc/de')

	assert '\\' not in youtube_dl._simplify_title('abc\\de')
	assert 'abc' in youtube_dl._simplify_title('abc\\de')
	assert 'de' in youtube_dl._simplify_title('abc\\de')

