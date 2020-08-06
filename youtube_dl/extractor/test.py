import time
import random
import requests
import sys
import getpass

def sign():#, username=_USERNAME, client_id=_CLIENT_ID, key=_KEY):
    zero = 0
    i = a = 1
    mA = 33
    u = 0 #u is actually screenWidth * screenHeight for 1920*1080 = 2073600
    mU = 2073600
    l = 1024 #1046?
    mL = 1028
    timestamp = millis = int(round(time.time() * 1000))
    mTimestamp = timestamp - (timestamp - random.randint(50000, 850000)) #hacky timestamp difference
    uTimestamp = random.randint(50000, 85000)
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
    t = _CLIENT_ID = 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'  #'T5R4kgWS2PRf6lzLyIravUMnKlbIxQag' #'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'


    p = n + y + d + r + e + t + d + n

    h = p

    print(h)

    m = 8011470
    f = 0 

    for f in range(f, len(h)):
        m = (m >> 1) + ((1 & m) << 23)
        m += ord(h[f])
        m &= 16777215

    out = str(y) + ':' + str(d) + ':' + format(m, 'x') + ':' + str(c)

    return out

#print(sign())

def signp(a, i, s, w, u, l, b, k, c, n, r, e, t):
    '''
    zero = 0
    i = a = 1
    mA = 33
    u = 0 #u is actually screenWidth * screenHeight for 1920*1080 = 2073600
    mU = 2073600
    l = 1024 #1046?
    mL = 1028
    timestamp = millis = int(round(time.time() * 1000))
    mTimestamp = timestamp - (timestamp - random.randint(50000, 850000)) #hacky timestamp difference
    uTimestamp = random.randint(50000, 85000)
    w = 42 #1049?
    mW = 1049
    b = k = 2 #25?
    mB = mK = 25
    underscore = 0 #4, 5?
    mUnderscore = 5
    '''

    d = '-'.join([str(mInt) for mInt in [a, i, s, w, u, l, b, k]])
    #d = '-'.join([str(mInt) for mInt in [mA, i, uTimestamp, mW, mU, mL, mB, mK]])
    #print(d)

    #c = mUnderscore

    #n = _KEY = '0763ed7314c69015fd4a0dc16bbf4b90'
    y = '8' #some kind of version??
    rr = _USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    ee = _USERNAME = "tom_heidel@web.de"
    tt = _CLIENT_ID = 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'  #'T5R4kgWS2PRf6lzLyIravUMnKlbIxQag' #'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'


    p = n + y + d + r + e + t + d + n

    h = p

    #print(h)

    m = 8011470
    f = 0 

    for f in range(f, len(h)):
        m = (m >> 1) + ((1 & m) << 23)
        m += ord(h[f])
        m &= 16777215
    
    #print(m)

    out = str(y) + ':' + str(d) + ':' + format(m, 'x') + ':' + str(c)

    return out

#sig = signp(33, 1, 193702, 748, 2073600, 1046, 2, 2, 4, "0763ed7314c69015fd4a0dc16bbf4b90", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", "tom_heidel@web.de", "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag")
#print(sig)
#print(signp(33, 1, -1, 748, 2073600, 1046, 2, 2, 4, "0763ed7314c69015fd4a0dc16bbf4b90", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", "tom_heidel@web.de", "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag"))
#print(signp(33, 1, 440123, 117, 1800000, 1042, 37, 37, 5, "0763ed7314c69015fd4a0dc16bbf4b90", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", "tom_heidel@web.de", "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag"))

#d = "33-1-193702-748-2073600-1046-2-2"
#p = "0763ed7314c69015fd4a0dc16bbf4b90833-1-193702-748-2073600-1046-2-2Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36tom_heidel@web.deT5R4kgWS2PRf6lzLyIravUMnKlbIxQag33-1-193702-748-2073600-1046-2-20763ed7314c69015fd4a0dc16bbf4b90"

#sig = "8:33-1-193702-748-2073600-1046-2-2:3bfb60:4"

login_form_hardcoded = {
            'client_id': "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag",
            'recaptcha_pubkey': 'null',
            'recaptcha_response': 'null',
            'credentials': {
                    'identifier': "tom_heidel@web.de",
                    'password': ''#getpass.getpass()
                },
            'signature': '',#sig,
            'device_id': '00000-000000-000000-000000',
            'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        }

user = input("User: ")
password = getpass.getpass()
sig_soft = signp(33, 1, 193702, 748, 2073600, 1046, 2, 2, 4, "0763ed7314c69015fd4a0dc16bbf4b90", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", user, "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag")

login_form_soft = {
            'client_id': "T5R4kgWS2PRf6lzLyIravUMnKlbIxQag",
            'recaptcha_pubkey': 'null',
            'recaptcha_response': 'null',
            'credentials': {
                    'identifier': user,
                    'password': password
                },
            'signature': sig_soft,
            'device_id': '00000-000000-000000-000000',
            'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        }

r = requests.post("https://api-auth.soundcloud.com/web-auth/sign-in/password?client_id=T5R4kgWS2PRf6lzLyIravUMnKlbIxQag", json=login_form_soft)
print(r.text)