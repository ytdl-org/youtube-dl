import time
import random

def sign():#, username=_USERNAME, client_id=_CLIENT_ID, key=_KEY):
    zero = 0
    i = a = 1
    mA = 33
    u = 0 #u is actually screenWidth * screenHeight for 1920*1080 = 2073600
    mU = 2073600
    l = 1024 #1046?
    mL = 1046
    timestamp = millis = int(round(time.time() * 1000))
    mTimestamp = timestamp - (timestamp - random.randint(50000, 850000)) #hacky timestamp difference
    uTimestamp = random.randint(50000, 850000)
    w = 42 #1049?
    mW = 1049
    b = k = 2 #25?
    mB = mK = 25
    underscore = 0 #4, 5?
    mUnderscore = 5


    #d = '-'.join([str(mInt) for mInt in [a, i, s, w, u, l, b, k]])
    d = '-'.join([str(mInt) for mInt in [mA, i, uTimestamp, mW, mU, mL, mB, mK]])
    print(d)

    c = mUnderscore

    n = _KEY = '0763ed7314c69015fd4a0dc16bbf4b90'
    y = '8' #some kind of version??
    r = _USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    e = _USERNAME = "tom_heidel@web.de"
    t = _CLIENT_ID = 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'


    p = n + y + d + r + e + t + d + n

    h = p

    m = 8011470
    f = 0 

    for f in range(f, len(h)):
        m = (m >> 1) + ((1 & m) << 23)
        m += ord(h[f])
        m &= 16777215

    out = str(y) + ':' + str(d) + ':' + format(m, 'x') + ':' + str(c)

    return out

print(sign())