# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.

youtube-dl	Download Page
Remember youtube-dl requires Python version 2.6, 2.7, or 3.2+ to work except for Windows exe.

Windows exe requires Microsoft Visual C++ 2010 Service Pack 1 Redistributable Package (x86) and does not require Python that is already embedded into the binary.

2021.12.17 (sig)
SHA256: 7880e01abe282c7fd596f429c35189851180d6177302bb215be1cdec78d6d06d

Windows exe (sig - SHA256 26e5c00c35c5c3edc86dfc0a720aed109a13b1b7c67ac654a0ce8ff82a1f2c16)
Full source + docs + binary tarball (sig - SHA256 9f3b99c8b778455165b4525f21505e86c7ff565f3ac319e19733d810194135df)

To install it right away for all UNIX users (Linux, OS X, etc.), type:
sudo curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl

sudo chmod a+rx /usr/local/bin/youtube-dl
If you do not have curl, you can alternatively use a recent wget:
sudo wget https://yt-dl.org/downloads/latest/youtube-dl -O /usr/local/bin/youtube-dl

sudo chmod a+rx /usr/local/bin/youtube-dl
You can also use pip:
sudo pip install --upgrade youtube_dl
This command will update youtube-dl if you have already installed it. See the pypi page for more information.

You can use Homebrew if you have it:
brew install youtube-dl
To check the signature, type:
sudo wget https://yt-dl.org/downloads/latest/youtube-dl.sig -O youtube-dl.sig
gpg --verify youtube-dl.sig /usr/local/bin/youtube-dl
rm youtube-dl.sig
The following GPG keys will be used to sign the binaries and the git tags:

Sergey M. ED7F 5BF4 6B3B BED8 1C87 368E 2C39 3E0F 18A9 236D
Older releases are also signed with one of:

Philipp Hagemeister 7D33 D762 FD6C 3513 0481 347F DB4B 54CB A482 6A18 (until 2016-05-30)
Philipp Hagemeister 0600 E1DB 6FB5 3A5D 95D8 FC0D F5EA B582 FAFB 085C (until 2013-06-01)
Filippo Valsorda 428D F5D6 3EF0 7494 BB45 5AC0 EBF0 1804 BCF0 5F6B (until 2014)
Creative Commons License
Copyright © 2006-2011 Ricardo Garcia Gonzalez
Copyright © 2011-2021 youtube-dl developers
