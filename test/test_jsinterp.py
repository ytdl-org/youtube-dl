#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import re

from youtube_dl.jsinterp import JS_Undefined, JSInterpreter


class TestJSInterpreter(unittest.TestCase):
    def test_basic(self):
        jsi = JSInterpreter('function x(){;}')
        self.assertEqual(jsi.call_function('x'), None)
        self.assertEqual(repr(jsi.extract_function('x')), 'F<x>')

        jsi = JSInterpreter('function x3(){return 42;}')
        self.assertEqual(jsi.call_function('x3'), 42)

        jsi = JSInterpreter('function x3(){42}')
        self.assertEqual(jsi.call_function('x3'), None)

        jsi = JSInterpreter('var x5 = function(){return 42;}')
        self.assertEqual(jsi.call_function('x5'), 42)

    def test_calc(self):
        jsi = JSInterpreter('function x4(a){return 2*a+1;}')
        self.assertEqual(jsi.call_function('x4', 3), 7)

    def test_add(self):
        jsi = JSInterpreter('function f(){return 42 + 7;}')
        self.assertEqual(jsi.call_function('f'), 49)
        jsi = JSInterpreter('function f(){return 42 + undefined;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))
        jsi = JSInterpreter('function f(){return 42 + null;}')
        self.assertEqual(jsi.call_function('f'), 42)

    def test_sub(self):
        jsi = JSInterpreter('function f(){return 42 - 7;}')
        self.assertEqual(jsi.call_function('f'), 35)
        jsi = JSInterpreter('function f(){return 42 - undefined;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))
        jsi = JSInterpreter('function f(){return 42 - null;}')
        self.assertEqual(jsi.call_function('f'), 42)

    def test_mul(self):
        jsi = JSInterpreter('function f(){return 42 * 7;}')
        self.assertEqual(jsi.call_function('f'), 294)
        jsi = JSInterpreter('function f(){return 42 * undefined;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))
        jsi = JSInterpreter('function f(){return 42 * null;}')
        self.assertEqual(jsi.call_function('f'), 0)

    def test_div(self):
        jsi = JSInterpreter('function f(a, b){return a / b;}')
        self.assertTrue(math.isnan(jsi.call_function('f', 0, 0)))
        self.assertTrue(math.isnan(jsi.call_function('f', JS_Undefined, 1)))
        self.assertTrue(math.isinf(jsi.call_function('f', 2, 0)))
        self.assertEqual(jsi.call_function('f', 0, 3), 0)

    def test_mod(self):
        jsi = JSInterpreter('function f(){return 42 % 7;}')
        self.assertEqual(jsi.call_function('f'), 0)
        jsi = JSInterpreter('function f(){return 42 % 0;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))
        jsi = JSInterpreter('function f(){return 42 % undefined;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))

    def test_exp(self):
        jsi = JSInterpreter('function f(){return 42 ** 2;}')
        self.assertEqual(jsi.call_function('f'), 1764)
        jsi = JSInterpreter('function f(){return 42 ** undefined;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))
        jsi = JSInterpreter('function f(){return 42 ** null;}')
        self.assertEqual(jsi.call_function('f'), 1)
        jsi = JSInterpreter('function f(){return undefined ** 42;}')
        self.assertTrue(math.isnan(jsi.call_function('f')))

    def test_empty_return(self):
        jsi = JSInterpreter('function f(){return; y()}')
        self.assertEqual(jsi.call_function('f'), None)

    def test_morespace(self):
        jsi = JSInterpreter('function x (a) { return 2 * a + 1 ; }')
        self.assertEqual(jsi.call_function('x', 3), 7)

        jsi = JSInterpreter('function f () { x =  2  ; return x; }')
        self.assertEqual(jsi.call_function('f'), 2)

    def test_strange_chars(self):
        jsi = JSInterpreter('function $_xY1 ($_axY1) { var $_axY2 = $_axY1 + 1; return $_axY2; }')
        self.assertEqual(jsi.call_function('$_xY1', 20), 21)

    def test_operators(self):
        jsi = JSInterpreter('function f(){return 1 << 5;}')
        self.assertEqual(jsi.call_function('f'), 32)

        jsi = JSInterpreter('function f(){return 2 ** 5}')
        self.assertEqual(jsi.call_function('f'), 32)

        jsi = JSInterpreter('function f(){return 19 & 21;}')
        self.assertEqual(jsi.call_function('f'), 17)

        jsi = JSInterpreter('function f(){return 11 >> 2;}')
        self.assertEqual(jsi.call_function('f'), 2)

        jsi = JSInterpreter('function f(){return []? 2+3: 4;}')
        self.assertEqual(jsi.call_function('f'), 5)

        jsi = JSInterpreter('function f(){return 1 == 2}')
        self.assertEqual(jsi.call_function('f'), False)

        jsi = JSInterpreter('function f(){return 0 && 1 || 2;}')
        self.assertEqual(jsi.call_function('f'), 2)

        jsi = JSInterpreter('function f(){return 0 ?? 42;}')
        self.assertEqual(jsi.call_function('f'), 0)

        jsi = JSInterpreter('function f(){return "life, the universe and everything" < 42;}')
        self.assertFalse(jsi.call_function('f'))

    def test_array_access(self):
        jsi = JSInterpreter('function f(){var x = [1,2,3]; x[0] = 4; x[0] = 5; x[2.0] = 7; return x;}')
        self.assertEqual(jsi.call_function('f'), [5, 2, 7])

    def test_parens(self):
        jsi = JSInterpreter('function f(){return (1) + (2) * ((( (( (((((3)))))) )) ));}')
        self.assertEqual(jsi.call_function('f'), 7)

        jsi = JSInterpreter('function f(){return (1 + 2) * 3;}')
        self.assertEqual(jsi.call_function('f'), 9)

    def test_quotes(self):
        jsi = JSInterpreter(r'function f(){return "a\"\\("}')
        self.assertEqual(jsi.call_function('f'), r'a"\(')

    def test_assignments(self):
        jsi = JSInterpreter('function f(){var x = 20; x = 30 + 1; return x;}')
        self.assertEqual(jsi.call_function('f'), 31)

        jsi = JSInterpreter('function f(){var x = 20; x += 30 + 1; return x;}')
        self.assertEqual(jsi.call_function('f'), 51)

        jsi = JSInterpreter('function f(){var x = 20; x -= 30 + 1; return x;}')
        self.assertEqual(jsi.call_function('f'), -11)

    def test_comments(self):
        'Skipping: Not yet fully implemented'
        return
        jsi = JSInterpreter('''
        function x() {
            var x = /* 1 + */ 2;
            var y = /* 30
            * 40 */ 50;
            return x + y;
        }
        ''')
        self.assertEqual(jsi.call_function('x'), 52)

        jsi = JSInterpreter('''
        function f() {
            var x = "/*";
            var y = 1 /* comment */ + 2;
            return y;
        }
        ''')
        self.assertEqual(jsi.call_function('f'), 3)

    def test_precedence(self):
        jsi = JSInterpreter('''
        function x() {
            var a = [10, 20, 30, 40, 50];
            var b = 6;
            a[0]=a[b%a.length];
            return a;
        }''')
        self.assertEqual(jsi.call_function('x'), [20, 20, 30, 40, 50])

    def test_builtins(self):
        jsi = JSInterpreter('''
        function x() { return NaN }
        ''')
        self.assertTrue(math.isnan(jsi.call_function('x')))

    def test_Date(self):
        jsi = JSInterpreter('''
        function x(dt) { return new Date(dt) - 0; }
        ''')
        self.assertEqual(jsi.call_function('x', 'Wednesday 31 December 1969 18:01:26 MDT'), 86000)

        # date format m/d/y
        self.assertEqual(jsi.call_function('x', '12/31/1969 18:01:26 MDT'), 86000)

        # epoch 0
        self.assertEqual(jsi.call_function('x', '1 January 1970 00:00:00 UTC'), 0)

    def test_call(self):
        jsi = JSInterpreter('''
        function x() { return 2; }
        function y(a) { return x() + (a?a:0); }
        function z() { return y(3); }
        ''')
        self.assertEqual(jsi.call_function('z'), 5)
        self.assertEqual(jsi.call_function('y'), 2)

    def test_if(self):
        jsi = JSInterpreter('''
        function x() {
            let a = 9;
            if (0==0) {a++}
            return a
        }''')
        self.assertEqual(jsi.call_function('x'), 10)

        jsi = JSInterpreter('''
        function x() {
            if (0==0) {return 10}
        }''')
        self.assertEqual(jsi.call_function('x'), 10)

        jsi = JSInterpreter('''
        function x() {
            if (0!=0) {return 1}
            else {return 10}
        }''')
        self.assertEqual(jsi.call_function('x'), 10)

        """  # Unsupported
        jsi = JSInterpreter('''
        function x() {
            if (0!=0) return 1;
            else {return 10}
        }''')
        self.assertEqual(jsi.call_function('x'), 10)
        """

    def test_elseif(self):
        jsi = JSInterpreter('''
        function x() {
            if (0!=0) {return 1}
            else if (1==0) {return 2}
            else {return 10}
        }''')
        self.assertEqual(jsi.call_function('x'), 10)

        """  # Unsupported
        jsi = JSInterpreter('''
        function x() {
            if (0!=0) return 1;
            else if (1==0) {return 2}
            else {return 10}
        }''')
        self.assertEqual(jsi.call_function('x'), 10)
        # etc
        """

    def test_for_loop(self):
        # function x() { a=0; for (i=0; i-10; i++) {a++} a }
        jsi = JSInterpreter('''
        function x() { a=0; for (i=0; i-10; i++) {a++} return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 10)

    def test_while_loop(self):
        # function x() { a=0; while (a<10) {a++} a }
        jsi = JSInterpreter('''
        function x() { a=0; while (a<10) {a++} return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 10)

    def test_switch(self):
        jsi = JSInterpreter('''
        function x(f) { switch(f){
            case 1:f+=1;
            case 2:f+=2;
            case 3:f+=3;break;
            case 4:f+=4;
            default:f=0;
        } return f }
        ''')
        self.assertEqual(jsi.call_function('x', 1), 7)
        self.assertEqual(jsi.call_function('x', 3), 6)
        self.assertEqual(jsi.call_function('x', 5), 0)

    def test_switch_default(self):
        jsi = JSInterpreter('''
        function x(f) { switch(f){
            case 2: f+=2;
            default: f-=1;
            case 5:
            case 6: f+=6;
            case 0: break;
            case 1: f+=1;
        } return f }
        ''')
        self.assertEqual(jsi.call_function('x', 1), 2)
        self.assertEqual(jsi.call_function('x', 5), 11)
        self.assertEqual(jsi.call_function('x', 9), 14)

    def test_try(self):
        jsi = JSInterpreter('''
        function x() { try{return 10} catch(e){return 5} }
        ''')
        self.assertEqual(jsi.call_function('x'), 10)

    def test_catch(self):
        jsi = JSInterpreter('''
        function x() { try{throw 10} catch(e){return 5} }
        ''')
        self.assertEqual(jsi.call_function('x'), 5)

    def test_finally(self):
        jsi = JSInterpreter('''
        function x() { try{throw 10} finally {return 42} }
        ''')
        self.assertEqual(jsi.call_function('x'), 42)
        jsi = JSInterpreter('''
        function x() { try{throw 10} catch(e){return 5} finally {return 42} }
        ''')
        self.assertEqual(jsi.call_function('x'), 42)

    def test_nested_try(self):
        jsi = JSInterpreter('''
        function x() {try {
            try{throw 10} finally {throw 42}
            } catch(e){return 5} }
        ''')
        self.assertEqual(jsi.call_function('x'), 5)

    def test_for_loop_continue(self):
        jsi = JSInterpreter('''
        function x() { a=0; for (i=0; i-10; i++) { continue; a++ } return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 0)

    def test_for_loop_break(self):
        jsi = JSInterpreter('''
        function x() { a=0; for (i=0; i-10; i++) { break; a++ } return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 0)

    def test_for_loop_try(self):
        jsi = JSInterpreter('''
        function x() {
            for (i=0; i-10; i++) { try { if (i == 5) throw i} catch {return 10} finally {break} };
            return 42 }
        ''')
        self.assertEqual(jsi.call_function('x'), 42)

    def test_literal_list(self):
        jsi = JSInterpreter('''
        function x() { return [1, 2, "asdf", [5, 6, 7]][3] }
        ''')
        self.assertEqual(jsi.call_function('x'), [5, 6, 7])

    def test_comma(self):
        jsi = JSInterpreter('''
        function x() { a=5; a -= 1, a+=3; return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 7)
        jsi = JSInterpreter('''
        function x() { a=5; return (a -= 1, a+=3, a); }
        ''')
        self.assertEqual(jsi.call_function('x'), 7)

        jsi = JSInterpreter('''
        function x() { return (l=[0,1,2,3], function(a, b){return a+b})((l[1], l[2]), l[3]) }
        ''')
        self.assertEqual(jsi.call_function('x'), 5)

    def test_void(self):
        jsi = JSInterpreter('''
        function x() { return void 42; }
        ''')
        self.assertEqual(jsi.call_function('x'), None)

    def test_return_function(self):
        jsi = JSInterpreter('''
        function x() { return [1, function(){return 1}][1] }
        ''')
        self.assertEqual(jsi.call_function('x')([]), 1)

    def test_null(self):
        jsi = JSInterpreter('''
        function x() { return null; }
        ''')
        self.assertIs(jsi.call_function('x'), None)

        jsi = JSInterpreter('''
        function x() { return [null > 0, null < 0, null == 0, null === 0]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, False, False, False])

        jsi = JSInterpreter('''
        function x() { return [null >= 0, null <= 0]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [True, True])

    def test_undefined(self):
        jsi = JSInterpreter('''
        function x() { return undefined === undefined; }
        ''')
        self.assertTrue(jsi.call_function('x'))

        jsi = JSInterpreter('''
        function x() { return undefined; }
        ''')
        self.assertIs(jsi.call_function('x'), JS_Undefined)

        jsi = JSInterpreter('''
        function x() { let v; return v; }
        ''')
        self.assertIs(jsi.call_function('x'), JS_Undefined)

        jsi = JSInterpreter('''
        function x() { return [undefined === undefined, undefined == undefined, undefined < undefined, undefined > undefined]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [True, True, False, False])

        jsi = JSInterpreter('''
        function x() { return [undefined === 0, undefined == 0, undefined < 0, undefined > 0]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, False, False, False])

        jsi = JSInterpreter('''
        function x() { return [undefined >= 0, undefined <= 0]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, False])

        jsi = JSInterpreter('''
        function x() { return [undefined > null, undefined < null, undefined == null, undefined === null]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, False, True, False])

        jsi = JSInterpreter('''
        function x() { return [undefined === null, undefined == null, undefined < null, undefined > null]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, True, False, False])

        jsi = JSInterpreter('''
        function x() { let v; return [42+v, v+42, v**42, 42**v, 0**v]; }
        ''')
        for y in jsi.call_function('x'):
            self.assertTrue(math.isnan(y))

        jsi = JSInterpreter('''
        function x() { let v; return v**0; }
        ''')
        self.assertEqual(jsi.call_function('x'), 1)

        jsi = JSInterpreter('''
        function x() { let v; return [v>42, v<=42, v&&42, 42&&v]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [False, False, JS_Undefined, JS_Undefined])

        jsi = JSInterpreter('function x(){return undefined ?? 42; }')
        self.assertEqual(jsi.call_function('x'), 42)

    def test_object(self):
        jsi = JSInterpreter('''
        function x() { return {}; }
        ''')
        self.assertEqual(jsi.call_function('x'), {})

        jsi = JSInterpreter('''
        function x() { let a = {m1: 42, m2: 0 }; return [a["m1"], a.m2]; }
        ''')
        self.assertEqual(jsi.call_function('x'), [42, 0])

        jsi = JSInterpreter('''
        function x() { let a; return a?.qq; }
        ''')
        self.assertIs(jsi.call_function('x'), JS_Undefined)

        jsi = JSInterpreter('''
        function x() { let a = {m1: 42, m2: 0 }; return a?.qq; }
        ''')
        self.assertIs(jsi.call_function('x'), JS_Undefined)

    def test_regex(self):
        jsi = JSInterpreter('''
        function x() { let a=/,,[/,913,/](,)}/; }
        ''')
        self.assertIs(jsi.call_function('x'), None)

        jsi = JSInterpreter('''
        function x() { let a=/,,[/,913,/](,)}/; "".replace(a, ""); return a; }
        ''')
        attrs = set(('findall', 'finditer', 'flags', 'groupindex',
                     'groups', 'match', 'pattern', 'scanner',
                     'search', 'split', 'sub', 'subn'))
        self.assertTrue(set(dir(jsi.call_function('x'))) > attrs)

        jsi = JSInterpreter('''
        function x() { let a=/,,[/,913,/](,)}/i; return a; }
        ''')
        self.assertEqual(jsi.call_function('x').flags & ~re.U, re.I)

        jsi = JSInterpreter(r'''
        function x() { let a="data-name".replace("data-", ""); return a }
        ''')
        self.assertEqual(jsi.call_function('x'), 'name')

        jsi = JSInterpreter(r'''
        function x() { let a="data-name".replace(new RegExp("^.+-"), ""); return a; }
        ''')
        self.assertEqual(jsi.call_function('x'), 'name')

        jsi = JSInterpreter(r'''
        function x() { let a="data-name".replace(/^.+-/, ""); return a; }
        ''')
        self.assertEqual(jsi.call_function('x'), 'name')

        jsi = JSInterpreter(r'''
        function x() { let a="data-name".replace(/a/g, "o"); return a; }
        ''')
        self.assertEqual(jsi.call_function('x'), 'doto-nome')

        jsi = JSInterpreter(r'''
        function x() { let a="data-name".replaceAll("a", "o"); return a; }
        ''')
        self.assertEqual(jsi.call_function('x'), 'doto-nome')

        jsi = JSInterpreter(r'''
        function x() { let a=[/[)\\]/]; return a[0]; }
        ''')
        self.assertEqual(jsi.call_function('x').pattern, r'[)\\]')

        """  # fails
        jsi = JSInterpreter(r'''
        function x() { let a=100; a/=/[0-9]+/.exec('divide by 20 today')[0]; }
        ''')
        self.assertEqual(jsi.call_function('x'), 5)
        """

    def test_char_code_at(self):
        jsi = JSInterpreter('function x(i){return "test".charCodeAt(i)}')
        self.assertEqual(jsi.call_function('x', 0), 116)
        self.assertEqual(jsi.call_function('x', 1), 101)
        self.assertEqual(jsi.call_function('x', 2), 115)
        self.assertEqual(jsi.call_function('x', 3), 116)
        self.assertEqual(jsi.call_function('x', 4), None)
        self.assertEqual(jsi.call_function('x', 'not_a_number'), 116)

    def test_bitwise_operators_overflow(self):
        jsi = JSInterpreter('function x(){return -524999584 << 5}')
        self.assertEqual(jsi.call_function('x'), 379882496)

        jsi = JSInterpreter('function x(){return 1236566549 << 5}')
        self.assertEqual(jsi.call_function('x'), 915423904)

    def test_bitwise_operators_madness(self):
        jsi = JSInterpreter('function x(){return null << 5}')
        self.assertEqual(jsi.call_function('x'), 0)

        jsi = JSInterpreter('function x(){return undefined >> 5}')
        self.assertEqual(jsi.call_function('x'), 0)

        jsi = JSInterpreter('function x(){return 42 << NaN}')
        self.assertEqual(jsi.call_function('x'), 42)

        jsi = JSInterpreter('function x(){return 42 << Infinity}')
        self.assertEqual(jsi.call_function('x'), 42)

    def test_32066(self):
        jsi = JSInterpreter("function x(){return Math.pow(3, 5) + new Date('1970-01-01T08:01:42.000+08:00') / 1000 * -239 - -24205;}")
        self.assertEqual(jsi.call_function('x'), 70)

    def test_unary_operators(self):
        jsi = JSInterpreter('function f(){return 2  -  - - 2;}')
        self.assertEqual(jsi.call_function('f'), 0)
        # fails
        # jsi = JSInterpreter('function f(){return 2 + - + - - 2;}')
        # self.assertEqual(jsi.call_function('f'), 0)

    """ # fails so far
    def test_packed(self):
        jsi = JSInterpreter('''function x(p,a,c,k,e,d){while(c--)if(k[c])p=p.replace(new RegExp('\\b'+c.toString(a)+'\\b','g'),k[c]);return p}''')
        self.assertEqual(jsi.call_function('x', '''h 7=g("1j");7.7h({7g:[{33:"w://7f-7e-7d-7c.v.7b/7a/79/78/77/76.74?t=73&s=2s&e=72&f=2t&71=70.0.0.1&6z=6y&6x=6w"}],6v:"w://32.v.u/6u.31",16:"r%",15:"r%",6t:"6s",6r:"",6q:"l",6p:"l",6o:"6n",6m:\'6l\',6k:"6j",9:[{33:"/2u?b=6i&n=50&6h=w://32.v.u/6g.31",6f:"6e"}],1y:{6d:1,6c:\'#6b\',6a:\'#69\',68:"67",66:30,65:r,},"64":{63:"%62 2m%m%61%5z%5y%5x.u%5w%5v%5u.2y%22 2k%m%1o%22 5t%m%1o%22 5s%m%1o%22 2j%m%5r%22 16%m%5q%22 15%m%5p%22 5o%2z%5n%5m%2z",5l:"w://v.u/d/1k/5k.2y",5j:[]},\'5i\':{"5h":"5g"},5f:"5e",5d:"w://v.u",5c:{},5b:l,1x:[0.25,0.50,0.75,1,1.25,1.5,2]});h 1m,1n,5a;h 59=0,58=0;h 7=g("1j");h 2x=0,57=0,56=0;$.55({54:{\'53-52\':\'2i-51\'}});7.j(\'4z\',6(x){c(5>0&&x.1l>=5&&1n!=1){1n=1;$(\'q.4y\').4x(\'4w\')}});7.j(\'13\',6(x){2x=x.1l});7.j(\'2g\',6(x){2w(x)});7.j(\'4v\',6(){$(\'q.2v\').4u()});6 2w(x){$(\'q.2v\').4t();c(1m)19;1m=1;17=0;c(4s.4r===l){17=1}$.4q(\'/2u?b=4p&2l=1k&4o=2t-4n-4m-2s-4l&4k=&4j=&4i=&17=\'+17,6(2r){$(\'#4h\').4g(2r)});$(\'.3-8-4f-4e:4d("4c")\').2h(6(e){2q();g().4b(0);g().4a(l)});6 2q(){h $14=$("<q />").2p({1l:"49",16:"r%",15:"r%",48:0,2n:0,2o:47,46:"45(10%, 10%, 10%, 0.4)","44-43":"42"});$("<41 />").2p({16:"60%",15:"60%",2o:40,"3z-2n":"3y"}).3x({\'2m\':\'/?b=3w&2l=1k\',\'2k\':\'0\',\'2j\':\'2i\'}).2f($14);$14.2h(6(){$(3v).3u();g().2g()});$14.2f($(\'#1j\'))}g().13(0);}6 3t(){h 9=7.1b(2e);2d.2c(9);c(9.n>1){1r(i=0;i<9.n;i++){c(9[i].1a==2e){2d.2c(\'!!=\'+i);7.1p(i)}}}}7.j(\'3s\',6(){g().1h("/2a/3r.29","3q 10 28",6(){g().13(g().27()+10)},"2b");$("q[26=2b]").23().21(\'.3-20-1z\');g().1h("/2a/3p.29","3o 10 28",6(){h 12=g().27()-10;c(12<0)12=0;g().13(12)},"24");$("q[26=24]").23().21(\'.3-20-1z\');});6 1i(){}7.j(\'3n\',6(){1i()});7.j(\'3m\',6(){1i()});7.j("k",6(y){h 9=7.1b();c(9.n<2)19;$(\'.3-8-3l-3k\').3j(6(){$(\'#3-8-a-k\').1e(\'3-8-a-z\');$(\'.3-a-k\').p(\'o-1f\',\'11\')});7.1h("/3i/3h.3g","3f 3e",6(){$(\'.3-1w\').3d(\'3-8-1v\');$(\'.3-8-1y, .3-8-1x\').p(\'o-1g\',\'11\');c($(\'.3-1w\').3c(\'3-8-1v\')){$(\'.3-a-k\').p(\'o-1g\',\'l\');$(\'.3-a-k\').p(\'o-1f\',\'l\');$(\'.3-8-a\').1e(\'3-8-a-z\');$(\'.3-8-a:1u\').3b(\'3-8-a-z\')}3a{$(\'.3-a-k\').p(\'o-1g\',\'11\');$(\'.3-a-k\').p(\'o-1f\',\'11\');$(\'.3-8-a:1u\').1e(\'3-8-a-z\')}},"39");7.j("38",6(y){1d.37(\'1c\',y.9[y.36].1a)});c(1d.1t(\'1c\')){35("1s(1d.1t(\'1c\'));",34)}});h 18;6 1s(1q){h 9=7.1b();c(9.n>1){1r(i=0;i<9.n;i++){c(9[i].1a==1q){c(i==18){19}18=i;7.1p(i)}}}}',36,270,'|||jw|||function|player|settings|tracks|submenu||if||||jwplayer|var||on|audioTracks|true|3D|length|aria|attr|div|100|||sx|filemoon|https||event|active||false|tt|seek|dd|height|width|adb|current_audio|return|name|getAudioTracks|default_audio|localStorage|removeClass|expanded|checked|addButton|callMeMaybe|vplayer|0fxcyc2ajhp1|position|vvplay|vvad|220|setCurrentAudioTrack|audio_name|for|audio_set|getItem|last|open|controls|playbackRates|captions|rewind|icon|insertAfter||detach|ff00||button|getPosition|sec|png|player8|ff11|log|console|track_name|appendTo|play|click|no|scrolling|frameborder|file_code|src|top|zIndex|css|showCCform|data|1662367683|383371|dl|video_ad|doPlay|prevt|mp4|3E||jpg|thumbs|file|300|setTimeout|currentTrack|setItem|audioTrackChanged|dualSound|else|addClass|hasClass|toggleClass|Track|Audio|svg|dualy|images|mousedown|buttons|topbar|playAttemptFailed|beforePlay|Rewind|fr|Forward|ff|ready|set_audio_track|remove|this|upload_srt|prop|50px|margin|1000001|iframe|center|align|text|rgba|background|1000000|left|absolute|pause|setCurrentCaptions|Upload|contains|item|content|html|fviews|referer|prem|embed|3e57249ef633e0d03bf76ceb8d8a4b65|216|83|hash|view|get|TokenZir|window|hide|show|complete|slow|fadeIn|video_ad_fadein|time||cache|Cache|Content|headers|ajaxSetup|v2done|tott|vastdone2|vastdone1|vvbefore|playbackRateControls|cast|aboutlink|FileMoon|abouttext|UHD|1870|qualityLabels|sites|GNOME_POWER|link|2Fiframe|3C|allowfullscreen|22360|22640|22no|marginheight|marginwidth|2FGNOME_POWER|2F0fxcyc2ajhp1|2Fe|2Ffilemoon|2F|3A||22https|3Ciframe|code|sharing|fontOpacity|backgroundOpacity|Tahoma|fontFamily|303030|backgroundColor|FFFFFF|color|userFontScale|thumbnails|kind|0fxcyc2ajhp10000|url|get_slides|start|startparam|none|preload|html5|primary|hlshtml|androidhls|duration|uniform|stretching|0fxcyc2ajhp1_xt|image|2048|sp|6871|asn|127|srv|43200|_g3XlBcu2lmD9oDexD2NLWSmah2Nu3XcDrl93m9PwXY|m3u8||master|0fxcyc2ajhp1_x|00076|01|hls2|to|s01|delivery|storage|moon|sources|setup'''.split('|')))
    """


if __name__ == '__main__':
    unittest.main()
