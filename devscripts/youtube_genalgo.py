#!/usr/bin/env python

# Generate youtube signature algorithm from test cases

import sys

tests = [
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<",
     "J:|}][{=+-_)(*&;%$#@>MNBVCXZASDFGH^KLPOIUYTREWQ0987654321mnbvcxzasdfghrklpoiuytej"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>.<",
     "!?;:|}][{=+-_)(*&^$#@/MNBVCXZASqFGHJKLPOIUYTREWQ0987654321mnbvcxzasdfghjklpoiuytr"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<",
     "ertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!/#$%^&*()_-+={[|};?@"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?/>.<",
     "{>/?;}[.=+-_)(*&^%$#@!MqBVCXZASDFwHJKLPOIUYTREWQ0987654321mnbvcxzasdfghjklpoiuytr"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?>.<",
     "<.>?;}[{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWe098765432rmnbvcxzasdfghjklpoiuyt1"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/>.<",
     "D.>/?;}[{=+_)(*&^%$#!MNBVCXeAS<FGHJKLPOIUYTREWZ0987654321mnbvcxzasdfghjklpoiuytrQ"),
    ("qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.<",
     "Q>/?;}[{=+-(*<^%$#@!MNBVCXZASDFGHKLPOIUY8REWT0q&7654321mnbvcxzasdfghjklpoiuytrew9"),
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

if __name__ == '__main__':
    main()
