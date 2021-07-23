#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import json
from youtube_dl.update import rsa_verify


class TestUpdate(unittest.TestCase):
    def test_rsa_verify(self):
        UPDATES_RSA_KEY = (
            0x9D60EE4D8F805312FDB15A62F87B95BD66177B91DF176765D13514A0F1754BCD2057295C5B6F1D35DAA6742C3FFC9A82D3E118861C207995A8031E151D863C9927E304576BC80692BC8E094896FCF11B66F3E29E04E3A71E9A11558558ACEA1840AEC37FC396FB6B65DC81A1C4144E03BD1C011DE62E3F1357B327D08426FE93,
            65537,
        )
        with open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions.json"),
            "rb",
        ) as f:
            versions_info = f.read().decode()
        versions_info = json.loads(versions_info)
        signature = versions_info["signature"]
        del versions_info["signature"]
        self.assertTrue(
            rsa_verify(
                json.dumps(versions_info, sort_keys=True).encode("utf-8"),
                signature,
                UPDATES_RSA_KEY,
            )
        )


if __name__ == "__main__":
    unittest.main()
