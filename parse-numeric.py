from __future__ import print_function
import math
import re

regex = re.compile(r'''(?:\s+)? # StrNumericLiteral.StrWhiteSpace (optional)
            ( # StringNumericLitral.StrDecimalLiteral
                (?P<inf_sign>[\+\-])? # optional sign
                (?P<inf>Infinity)|
                [\+\-]?(?P<nan>NaN)|  # not documented, but Node returns NaN
                [\+\-]?(?:  # DecimalDigits . DecimalDigits(opt) ExponentPart(opt)
                    (?:\d+)? # DecimalDigits
                    (?:\.)
                    (?:\d+)? # DecimalDigits
                    (?:[eE] # ExponentPart.ExponentIndicator
                        [\+\=]?  # optional sign
                        (?:\d+)
                    )?
                )|
                0(?P<binary>[bB])(?P<binary_number>[01]+)|
                0(?P<octal>[oO])(?P<octal_number>[01234567]+)|
                0(?P<hex>[xX])(?P<hex_number>[0-9a-fA-F]+)
            )(?:\s+)?$''', re.X)


def getnan():
    try:
        return math.nan
    except AttributeError:
        pass
    return float('nan')


def getinf(mult=1):
    try:
        ret = math.inf
    except AttributeError:
        ret = float('inf')
    return mult * ret


def can_be_int(inp, out):
    return str(out)[-2:] == '.0' and ('.0' not in inp and not inp.endswith('.'))


def conditional_int(inp):
    # Values with leading zeros like 01.0 and 01. should fail
    if len(inp) > 1 and inp[0] == '0':
        raise SyntaxError('unexpected number; given "{}"'.format(inp))
    out = float(inp)
    return int(str(out)[:-2], 10) if can_be_int(inp, out) else out


def parse_numeric(x):
    m = re.match(regex, x)
    if not m:
        raise SyntaxError('invalid nor unexpected token; given "{}"'.format(x))

    ret = m.group(0).strip()
    groups = m.groupdict()

    if groups['inf']:
        sign = -1 if groups['inf_sign'] == '-' else 1
        ret = getinf(sign)
    elif groups['nan']:
        ret = getnan()
    else:
        base = key = None
        if groups['binary']:
            base = 2
            key = 'binary_number'
        elif groups['octal']:
            base = 8
            key = 'octal_number'
        elif groups['hex']:
            base = 16
            key = 'hex_number'
        if key and base:
            ret = int(groups[key], base)
        else:
            try:
                ret = conditional_int(ret)
            except ValueError as e:
                raise SyntaxError('invalid or unexpected token: given "{}"'.format(x))
    print('{} -> {}'.format(x, ret))
    return ret

parse_numeric('.1')
parse_numeric('1.')
parse_numeric('Infinity')
parse_numeric('-Infinity')
parse_numeric('+Infinity')
parse_numeric('NaN')
parse_numeric('-NaN')
parse_numeric('+NaN')
try:
    parse_numeric('01.0')
except SyntaxError as e:
    print('01.0 -> {}'.format(e))
try:
    parse_numeric('01.')
except SyntaxError as e:
    print('01. -> {}'.format(e))
parse_numeric('1.0')
parse_numeric('1.1')
parse_numeric('1.e5')
parse_numeric('1.E5')
parse_numeric('1.1e5')
parse_numeric('1.1E6')
parse_numeric('-1.1E6')
parse_numeric('+1.1')
parse_numeric('0b101')
parse_numeric('0B101')
parse_numeric('0o755')
parse_numeric('0O755')
parse_numeric('0xaf')
parse_numeric('0XDEADBEEF9')
