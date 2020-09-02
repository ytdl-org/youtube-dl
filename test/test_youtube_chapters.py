#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import expect_value
from youtube_dlc.extractor import YoutubeIE


class TestYoutubeChapters(unittest.TestCase):

    _TEST_CASES = [
        (
            # https://www.youtube.com/watch?v=A22oy8dFjqc
            # pattern: 00:00 - <title>
            '''This is the absolute ULTIMATE experience of Queen's set at LIVE AID, this is the best video mixed to the absolutely superior stereo radio broadcast. This vastly superior audio mix takes a huge dump on all of the official mixes. Best viewed in 1080p. ENJOY! ***MAKE SURE TO READ THE DESCRIPTION***<br /><a href="#" onclick="yt.www.watch.player.seekTo(00*60+36);return false;">00:36</a> - Bohemian Rhapsody<br /><a href="#" onclick="yt.www.watch.player.seekTo(02*60+42);return false;">02:42</a> - Radio Ga Ga<br /><a href="#" onclick="yt.www.watch.player.seekTo(06*60+53);return false;">06:53</a> - Ay Oh!<br /><a href="#" onclick="yt.www.watch.player.seekTo(07*60+34);return false;">07:34</a> - Hammer To Fall<br /><a href="#" onclick="yt.www.watch.player.seekTo(12*60+08);return false;">12:08</a> - Crazy Little Thing Called Love<br /><a href="#" onclick="yt.www.watch.player.seekTo(16*60+03);return false;">16:03</a> - We Will Rock You<br /><a href="#" onclick="yt.www.watch.player.seekTo(17*60+18);return false;">17:18</a> - We Are The Champions<br /><a href="#" onclick="yt.www.watch.player.seekTo(21*60+12);return false;">21:12</a> - Is This The World We Created...?<br /><br />Short song analysis:<br /><br />- "Bohemian Rhapsody": Although it's a short medley version, it's one of the best performances of the ballad section, with Freddie nailing the Bb4s with the correct studio phrasing (for the first time ever!).<br /><br />- "Radio Ga Ga": Although it's missing one chorus, this is one of - if not the best - the best versions ever, Freddie nails all the Bb4s and sounds very clean! Spike Edney's Roland Jupiter 8 also really shines through on this mix, compared to the DVD releases!<br /><br />- "Audience Improv": A great improv, Freddie sounds strong and confident. You gotta love when he sustains that A4 for 4 seconds!<br /><br />- "Hammer To Fall": Despite missing a verse and a chorus, it's a strong version (possibly the best ever). Freddie sings the song amazingly, and even ad-libs a C#5 and a C5! Also notice how heavy Brian's guitar sounds compared to the thin DVD mixes - it roars!<br /><br />- "Crazy Little Thing Called Love": A great version, the crowd loves the song, the jam is great as well! Only downside to this is the slight feedback issues.<br /><br />- "We Will Rock You": Although cut down to the 1st verse and chorus, Freddie sounds strong. He nails the A4, and the solo from Dr. May is brilliant!<br /><br />- "We Are the Champions": Perhaps the high-light of the performance - Freddie is very daring on this version, he sustains the pre-chorus Bb4s, nails the 1st C5, belts great A4s, but most importantly: He nails the chorus Bb4s, in all 3 choruses! This is the only time he has ever done so! It has to be said though, the last one sounds a bit rough, but that's a side effect of belting high notes for the past 18 minutes, with nodules AND laryngitis!<br /><br />- "Is This The World We Created... ?": Freddie and Brian perform a beautiful version of this, and it is one of the best versions ever. It's both sad and hilarious that a couple of BBC engineers are talking over the song, one of them being completely oblivious of the fact that he is interrupting the performance, on live television... Which was being televised to almost 2 billion homes.<br /><br /><br />All rights go to their respective owners!<br />-----Copyright Disclaimer Under Section 107 of the Copyright Act 1976, allowance is made for fair use for purposes such as criticism, comment, news reporting, teaching, scholarship, and research. Fair use is a use permitted by copyright statute that might otherwise be infringing. Non-profit, educational or personal use tips the balance in favor of fair use''',
            1477,
            [{
                'start_time': 36,
                'end_time': 162,
                'title': 'Bohemian Rhapsody',
            }, {
                'start_time': 162,
                'end_time': 413,
                'title': 'Radio Ga Ga',
            }, {
                'start_time': 413,
                'end_time': 454,
                'title': 'Ay Oh!',
            }, {
                'start_time': 454,
                'end_time': 728,
                'title': 'Hammer To Fall',
            }, {
                'start_time': 728,
                'end_time': 963,
                'title': 'Crazy Little Thing Called Love',
            }, {
                'start_time': 963,
                'end_time': 1038,
                'title': 'We Will Rock You',
            }, {
                'start_time': 1038,
                'end_time': 1272,
                'title': 'We Are The Champions',
            }, {
                'start_time': 1272,
                'end_time': 1477,
                'title': 'Is This The World We Created...?',
            }]
        ),
        (
            # https://www.youtube.com/watch?v=ekYlRhALiRQ
            # pattern: <num>. <title> 0:00
            '1.  Those Beaten Paths of Confusion <a href="#" onclick="yt.www.watch.player.seekTo(0*60+00);return false;">0:00</a><br />2.  Beyond the Shadows of Emptiness & Nothingness <a href="#" onclick="yt.www.watch.player.seekTo(11*60+47);return false;">11:47</a><br />3.  Poison Yourself...With Thought <a href="#" onclick="yt.www.watch.player.seekTo(26*60+30);return false;">26:30</a><br />4.  The Agents of Transformation <a href="#" onclick="yt.www.watch.player.seekTo(35*60+57);return false;">35:57</a><br />5.  Drowning in the Pain of Consciousness <a href="#" onclick="yt.www.watch.player.seekTo(44*60+32);return false;">44:32</a><br />6.  Deny the Disease of Life <a href="#" onclick="yt.www.watch.player.seekTo(53*60+07);return false;">53:07</a><br /><br />More info/Buy: http://crepusculonegro.storenvy.com/products/257645-cn-03-arizmenda-within-the-vacuum-of-infinity<br /><br />No copyright is intended. The rights to this video are assumed by the owner and its affiliates.',
            4009,
            [{
                'start_time': 0,
                'end_time': 707,
                'title': '1. Those Beaten Paths of Confusion',
            }, {
                'start_time': 707,
                'end_time': 1590,
                'title': '2. Beyond the Shadows of Emptiness & Nothingness',
            }, {
                'start_time': 1590,
                'end_time': 2157,
                'title': '3. Poison Yourself...With Thought',
            }, {
                'start_time': 2157,
                'end_time': 2672,
                'title': '4. The Agents of Transformation',
            }, {
                'start_time': 2672,
                'end_time': 3187,
                'title': '5. Drowning in the Pain of Consciousness',
            }, {
                'start_time': 3187,
                'end_time': 4009,
                'title': '6. Deny the Disease of Life',
            }]
        ),
        (
            # https://www.youtube.com/watch?v=WjL4pSzog9w
            # pattern: 00:00 <title>
            '<a href="https://arizmenda.bandcamp.com/merch/despairs-depths-descended-cd" class="yt-uix-servicelink  " data-target-new-window="True" data-servicelink="CDAQ6TgYACITCNf1raqT2dMCFdRjGAod_o0CBSj4HQ" data-url="https://arizmenda.bandcamp.com/merch/despairs-depths-descended-cd" rel="nofollow noopener" target="_blank">https://arizmenda.bandcamp.com/merch/...</a><br /><br /><a href="#" onclick="yt.www.watch.player.seekTo(00*60+00);return false;">00:00</a> Christening Unborn Deformities <br /><a href="#" onclick="yt.www.watch.player.seekTo(07*60+08);return false;">07:08</a> Taste of Purity<br /><a href="#" onclick="yt.www.watch.player.seekTo(16*60+16);return false;">16:16</a> Sculpting Sins of a Universal Tongue<br /><a href="#" onclick="yt.www.watch.player.seekTo(24*60+45);return false;">24:45</a> Birth<br /><a href="#" onclick="yt.www.watch.player.seekTo(31*60+24);return false;">31:24</a> Neves<br /><a href="#" onclick="yt.www.watch.player.seekTo(37*60+55);return false;">37:55</a> Libations in Limbo',
            2705,
            [{
                'start_time': 0,
                'end_time': 428,
                'title': 'Christening Unborn Deformities',
            }, {
                'start_time': 428,
                'end_time': 976,
                'title': 'Taste of Purity',
            }, {
                'start_time': 976,
                'end_time': 1485,
                'title': 'Sculpting Sins of a Universal Tongue',
            }, {
                'start_time': 1485,
                'end_time': 1884,
                'title': 'Birth',
            }, {
                'start_time': 1884,
                'end_time': 2275,
                'title': 'Neves',
            }, {
                'start_time': 2275,
                'end_time': 2705,
                'title': 'Libations in Limbo',
            }]
        ),
        (
            # https://www.youtube.com/watch?v=o3r1sn-t3is
            # pattern: <title> 00:00 <note>
            'Download this show in MP3: <a href="http://sh.st/njZKK" class="yt-uix-servicelink  " data-url="http://sh.st/njZKK" data-target-new-window="True" data-servicelink="CDAQ6TgYACITCK3j8_6o2dMCFVDCGAoduVAKKij4HQ" rel="nofollow noopener" target="_blank">http://sh.st/njZKK</a><br /><br />Setlist:<br />I-E-A-I-A-I-O <a href="#" onclick="yt.www.watch.player.seekTo(00*60+45);return false;">00:45</a><br />Suite-Pee <a href="#" onclick="yt.www.watch.player.seekTo(4*60+26);return false;">4:26</a>  (Incomplete)<br />Attack <a href="#" onclick="yt.www.watch.player.seekTo(5*60+31);return false;">5:31</a> (First live performance since 2011)<br />Prison Song <a href="#" onclick="yt.www.watch.player.seekTo(8*60+42);return false;">8:42</a><br />Know <a href="#" onclick="yt.www.watch.player.seekTo(12*60+32);return false;">12:32</a> (First live performance since 2011)<br />Aerials <a href="#" onclick="yt.www.watch.player.seekTo(15*60+32);return false;">15:32</a><br />Soldier Side - Intro <a href="#" onclick="yt.www.watch.player.seekTo(19*60+13);return false;">19:13</a><br />B.Y.O.B. <a href="#" onclick="yt.www.watch.player.seekTo(20*60+09);return false;">20:09</a><br />Soil <a href="#" onclick="yt.www.watch.player.seekTo(24*60+32);return false;">24:32</a><br />Darts <a href="#" onclick="yt.www.watch.player.seekTo(27*60+48);return false;">27:48</a><br />Radio/Video <a href="#" onclick="yt.www.watch.player.seekTo(30*60+38);return false;">30:38</a><br />Hypnotize <a href="#" onclick="yt.www.watch.player.seekTo(35*60+05);return false;">35:05</a><br />Temper <a href="#" onclick="yt.www.watch.player.seekTo(38*60+08);return false;">38:08</a> (First live performance since 1999)<br />CUBErt <a href="#" onclick="yt.www.watch.player.seekTo(41*60+00);return false;">41:00</a><br />Needles <a href="#" onclick="yt.www.watch.player.seekTo(42*60+57);return false;">42:57</a><br />Deer Dance <a href="#" onclick="yt.www.watch.player.seekTo(46*60+27);return false;">46:27</a><br />Bounce <a href="#" onclick="yt.www.watch.player.seekTo(49*60+38);return false;">49:38</a><br />Suggestions <a href="#" onclick="yt.www.watch.player.seekTo(51*60+25);return false;">51:25</a><br />Psycho <a href="#" onclick="yt.www.watch.player.seekTo(53*60+52);return false;">53:52</a><br />Chop Suey! <a href="#" onclick="yt.www.watch.player.seekTo(58*60+13);return false;">58:13</a><br />Lonely Day <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+01*60+15);return false;">1:01:15</a><br />Question! <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+04*60+14);return false;">1:04:14</a><br />Lost in Hollywood <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+08*60+10);return false;">1:08:10</a><br />Vicinity of Obscenity  <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+13*60+40);return false;">1:13:40</a>(First live performance since 2012)<br />Forest <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+16*60+17);return false;">1:16:17</a><br />Cigaro <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+20*60+02);return false;">1:20:02</a><br />Toxicity <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+23*60+57);return false;">1:23:57</a>(with Chino Moreno)<br />Sugar <a href="#" onclick="yt.www.watch.player.seekTo(1*3600+27*60+53);return false;">1:27:53</a>',
            5640,
            [{
                'start_time': 45,
                'end_time': 266,
                'title': 'I-E-A-I-A-I-O',
            }, {
                'start_time': 266,
                'end_time': 331,
                'title': 'Suite-Pee (Incomplete)',
            }, {
                'start_time': 331,
                'end_time': 522,
                'title': 'Attack (First live performance since 2011)',
            }, {
                'start_time': 522,
                'end_time': 752,
                'title': 'Prison Song',
            }, {
                'start_time': 752,
                'end_time': 932,
                'title': 'Know (First live performance since 2011)',
            }, {
                'start_time': 932,
                'end_time': 1153,
                'title': 'Aerials',
            }, {
                'start_time': 1153,
                'end_time': 1209,
                'title': 'Soldier Side - Intro',
            }, {
                'start_time': 1209,
                'end_time': 1472,
                'title': 'B.Y.O.B.',
            }, {
                'start_time': 1472,
                'end_time': 1668,
                'title': 'Soil',
            }, {
                'start_time': 1668,
                'end_time': 1838,
                'title': 'Darts',
            }, {
                'start_time': 1838,
                'end_time': 2105,
                'title': 'Radio/Video',
            }, {
                'start_time': 2105,
                'end_time': 2288,
                'title': 'Hypnotize',
            }, {
                'start_time': 2288,
                'end_time': 2460,
                'title': 'Temper (First live performance since 1999)',
            }, {
                'start_time': 2460,
                'end_time': 2577,
                'title': 'CUBErt',
            }, {
                'start_time': 2577,
                'end_time': 2787,
                'title': 'Needles',
            }, {
                'start_time': 2787,
                'end_time': 2978,
                'title': 'Deer Dance',
            }, {
                'start_time': 2978,
                'end_time': 3085,
                'title': 'Bounce',
            }, {
                'start_time': 3085,
                'end_time': 3232,
                'title': 'Suggestions',
            }, {
                'start_time': 3232,
                'end_time': 3493,
                'title': 'Psycho',
            }, {
                'start_time': 3493,
                'end_time': 3675,
                'title': 'Chop Suey!',
            }, {
                'start_time': 3675,
                'end_time': 3854,
                'title': 'Lonely Day',
            }, {
                'start_time': 3854,
                'end_time': 4090,
                'title': 'Question!',
            }, {
                'start_time': 4090,
                'end_time': 4420,
                'title': 'Lost in Hollywood',
            }, {
                'start_time': 4420,
                'end_time': 4577,
                'title': 'Vicinity of Obscenity (First live performance since 2012)',
            }, {
                'start_time': 4577,
                'end_time': 4802,
                'title': 'Forest',
            }, {
                'start_time': 4802,
                'end_time': 5037,
                'title': 'Cigaro',
            }, {
                'start_time': 5037,
                'end_time': 5273,
                'title': 'Toxicity (with Chino Moreno)',
            }, {
                'start_time': 5273,
                'end_time': 5640,
                'title': 'Sugar',
            }]
        ),
        (
            # https://www.youtube.com/watch?v=PkYLQbsqCE8
            # pattern: <num> - <title> [<latinized title>] 0:00:00
            '''Затемно (Zatemno) is an Obscure Black Metal Band from Russia.<br /><br />"Во прах (Vo prakh)'' Into The Ashes", Debut mini-album released may 6, 2016, by Death Knell Productions<br />Released on 6 panel digipak CD, limited to 100 copies only<br />And digital format on Bandcamp<br /><br />Tracklist<br /><br />1 - Во прах [Vo prakh] <a href="#" onclick="yt.www.watch.player.seekTo(0*3600+00*60+00);return false;">0:00:00</a><br />2 - Искупление [Iskupleniye] <a href="#" onclick="yt.www.watch.player.seekTo(0*3600+08*60+10);return false;">0:08:10</a><br />3 - Из серпов луны...[Iz serpov luny] <a href="#" onclick="yt.www.watch.player.seekTo(0*3600+14*60+30);return false;">0:14:30</a><br /><br />Links:<br /><a href="https://deathknellprod.bandcamp.com/album/--2" class="yt-uix-servicelink  " data-target-new-window="True" data-url="https://deathknellprod.bandcamp.com/album/--2" data-servicelink="CC8Q6TgYACITCNP234Kr2dMCFcNxGAodQqsIwSj4HQ" target="_blank" rel="nofollow noopener">https://deathknellprod.bandcamp.com/a...</a><br /><a href="https://www.facebook.com/DeathKnellProd/" class="yt-uix-servicelink  " data-target-new-window="True" data-url="https://www.facebook.com/DeathKnellProd/" data-servicelink="CC8Q6TgYACITCNP234Kr2dMCFcNxGAodQqsIwSj4HQ" target="_blank" rel="nofollow noopener">https://www.facebook.com/DeathKnellProd/</a><br /><br /><br />I don't have any right about this artifact, my only intention is to spread the music of the band, all rights are reserved to the Затемно (Zatemno) and his producers, Death Knell Productions.<br /><br />------------------------------------------------------------------<br /><br />Subscribe for more videos like this.<br />My link: <a href="https://web.facebook.com/AttackOfTheDragons" class="yt-uix-servicelink  " data-target-new-window="True" data-url="https://web.facebook.com/AttackOfTheDragons" data-servicelink="CC8Q6TgYACITCNP234Kr2dMCFcNxGAodQqsIwSj4HQ" target="_blank" rel="nofollow noopener">https://web.facebook.com/AttackOfTheD...</a>''',
            1138,
            [{
                'start_time': 0,
                'end_time': 490,
                'title': '1 - Во прах [Vo prakh]',
            }, {
                'start_time': 490,
                'end_time': 870,
                'title': '2 - Искупление [Iskupleniye]',
            }, {
                'start_time': 870,
                'end_time': 1138,
                'title': '3 - Из серпов луны...[Iz serpov luny]',
            }]
        ),
        (
            # https://www.youtube.com/watch?v=xZW70zEasOk
            # time point more than duration
            '''● LCS Spring finals: Saturday and Sunday from <a href="#" onclick="yt.www.watch.player.seekTo(13*60+30);return false;">13:30</a> outside the venue! <br />● PAX East: Fri, Sat & Sun - more info in tomorrows video on the main channel!''',
            283,
            []
        ),
    ]

    def test_youtube_chapters(self):
        for description, duration, expected_chapters in self._TEST_CASES:
            ie = YoutubeIE()
            expect_value(
                self, ie._extract_chapters_from_description(description, duration),
                expected_chapters, None)


if __name__ == '__main__':
    unittest.main()
