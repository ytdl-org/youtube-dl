#!/usr/bin/env python

# Execute with
# $ python youtube_dl/__main__.py (2.6+)
# $ python -m youtube_dl          (2.7+)

import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    import os.path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_dl

if __name__ == '__main__':
    youtube_dl.main()
