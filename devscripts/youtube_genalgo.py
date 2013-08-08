#!/usr/bin/env python

# Generate youtube signature algorithm from test cases

import sys

tests = [
    # 92 - vflQw-fB4 2013/07/17
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`~\"",
     "mrtyuioplkjhgfdsazxcvbnq1234567890QWERTY}IOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]\"|:;"),
    # 90
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`",
     "mrtyuioplkjhgfdsazxcvbne1234567890QWER[YUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={`]}|"),
    # 88
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<",
     "J:|}][{=+-_)(*&;%$#@>MNBVCXZASDFGH^KLPOIUYTREWQ0987654321mnbvcxzasdfghrklpoiuytej"),
    # 87 - vflART1Nf 2013/07/24
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>.<",
     "tyuioplkjhgfdsazxcv<nm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>"),
    # 86 - vflm_D8eE 2013/07/31
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<",
     ">.1}|[{=+-_)(*&^%$#@!MNBVCXZASDFGHJK<POIUYTREW509876L432/mnbvcxzasdfghjklpoiuytre"),
    # 85 - vflSAFCP9 2013/07/19
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?/>.<",
     "ertyuiqplkjhgfdsazx$vbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#<%^&*()_-+={[};?/c"),
    # 84
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?>.<",
     "<.>?;}[{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWe098765432rmnbvcxzasdfghjklpoiuyt1"),
    # 83 - vflTWC9KW 2013/08/01
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/>.<",
     "qwertyuioplkjhg>dsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/f"),
    # 82
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.<",
     "Q>/?;}[{=+-(*<^%$#@!MNBVCXZASDFGHKLPOIUY8REWT0q&7654321mnbvcxzasdfghjklpoiuytrew9"),
    # 81 - vflLC8JvQ 2013/07/25
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.",
     "C>/?;}[{=+-(*&^%$#@!MNBVYXZASDFGHKLPOIU.TREWQ0q87659321mnbvcxzasdfghjkl4oiuytrewp"),
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
