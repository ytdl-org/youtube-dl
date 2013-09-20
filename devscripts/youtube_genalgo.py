#!/usr/bin/env python
# encoding: utf-8

# Generate youtube signature algorithm from test cases

import sys

tests = [
    # 93 - vfl79wBKW 2013/07/20
    (u"qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`~\"€",
     u".>/?;:|}][{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWQ098765'321mnbvcxzasdfghjklpoiu"),
    # 92 - vflQw-fB4 2013/07/17
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`~\"",
     "mrtyuioplkjhgfdsazxcvbnq1234567890QWERTY}IOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]\"|:;"),
    # 91 - vfl79wBKW 2013/07/20 (sporadic)
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`~",
     "/?;:|}][{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWQ09876543.1mnbvcxzasdfghjklpoiu"),
    # 90
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`",
     "mrtyuioplkjhgfdsazxcvbne1234567890QWER[YUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={`]}|"),
    # 89 
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'",
     "/?;:|}<[{=+-_)(*&^%$#@!MqBVCXZASDFGHJKLPOIUYTREWQ0987654321mnbvcxzasdfghjklpoiuyt"),
    # 88 - vflapUV9V 2013/08/28
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<",
     "ioplkjhgfdsazxcvbnm12<4567890QWERTYUIOZLKJHGFDSAeXCVBNM!@#$%^&*()_-+={[]}|:;?/>.3"),
    # 87
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>.<",
     "uioplkjhgfdsazxcvbnm1t34567890QWE2TYUIOPLKJHGFDSAZXCVeNM!@#$^&*()_-+={[]}|:;?/>.<"),
    # 86 - vfluy6kdb 2013/09/06
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<",
     "yuioplkjhgfdsazxcvbnm12345678q0QWrRTYUIOELKJHGFD-AZXCVBNM!@#$%^&*()_<+={[|};?/>.S"),
    # 85 - vflkuzxcs 2013/09/11
    ('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[',
     '3456789a0cdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRS[UVWXYZ!"#$%&\'()*+,-./:;<=>?@'),
    # 84 - vflg0g8PQ 2013/08/29 (sporadic)
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?>.<",
     ">?;}[{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWq0987654321mnbvcxzasdfghjklpoiuytr"),
    # 83
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/>.<",
     ".>/?;}[{=+_)(*&^%<#!MNBVCXZASPFGHJKLwOIUYTREWQ0987654321mnbvcxzasdfghjklpoiuytreq"),
    # 82 - vflGNjMhJ 2013/09/12
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.<",
     ".>/?;}[<=+-(*&^%$#@!MNBVCXeASDFGHKLPOqUYTREWQ0987654321mnbvcxzasdfghjklpoiuytrIwZ"),
    # 81 - vflLC8JvQ 2013/07/25
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.",
     "C>/?;}[{=+-(*&^%$#@!MNBVYXZASDFGHKLPOIU.TREWQ0q87659321mnbvcxzasdfghjkl4oiuytrewp"),
    # 80 - vflZK4ZYR 2013/08/23 (sporadic)
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>",
     "wertyuioplkjhgfdsaqxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&z(-+={[};?/>"),
    # 79 - vflLC8JvQ 2013/07/25 (sporadic)
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/",
     "Z?;}[{=+-(*&^%$#@!MNBVCXRASDFGHKLPOIUYT/EWQ0q87659321mnbvcxzasdfghjkl4oiuytrewp"),
]

tests_age_gate = [
    # 86 - vflqinMWD
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<",
     "ertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!/#$%^&*()_-+={[|};?@"),
]

def find_matching(wrong, right):
    idxs = [wrong.index(c) for c in right]
    return compress(idxs)
    return ('s[%d]' % i for i in idxs)

def compress(idxs):
    def _genslice(start, end, step):
        starts = '' if start == 0 else str(start)
        ends = ':%d' % (end+step)
        steps = '' if step == 1 else (':%d' % step)
        return 's[%s%s%s]' % (starts, ends, steps)

    step = None
    for i, prev in zip(idxs[1:], idxs[:-1]):
        if step is not None:
            if i - prev == step:
                continue
            yield _genslice(start, prev, step)
            step = None
            continue
        if i - prev in [-1, 1]:
            step = i - prev
            start = prev
            continue
        else:
            yield 's[%d]' % prev
    if step is None:
        yield 's[%d]' % i
    else:
        yield _genslice(start, i, step)

def _assert_compress(inp, exp):
    res = list(compress(inp))
    if res != exp:
        print('Got %r, expected %r' % (res, exp))
        assert res == exp
_assert_compress([0,2,4,6], ['s[0]', 's[2]', 's[4]', 's[6]'])
_assert_compress([0,1,2,4,6,7], ['s[:3]', 's[4]', 's[6:8]'])
_assert_compress([8,0,1,2,4,7,6,9], ['s[8]', 's[:3]', 's[4]', 's[7:5:-1]', 's[9]'])

def gen(wrong, right, indent):
    code = ' + '.join(find_matching(wrong, right))
    return 'if len(s) == %d:\n%s    return %s\n' % (len(wrong), indent, code)

def genall(tests):
    indent = ' ' * 8
    return indent + (indent + 'el').join(gen(wrong, right, indent) for wrong,right in tests)

def main():
    print(genall(tests))
    print(u'    Age gate:')
    print(genall(tests_age_gate))

if __name__ == '__main__':
    main()
