# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import ExtractorError, parse_iso8601
from ..compat import compat_HTTPError
import re


class NhkRadioBase(InfoExtractor):
    def _get_json_meta(self, program_id, corner_id):
        program_corner_id = program_id + "_" + corner_id
        try:
            data = self._download_json(
                "https://www.nhk.or.jp/radioondemand/json/"
                + program_id
                + "/bangumi_"
                + program_corner_id
                + ".json",
                program_corner_id,
            )
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                raise ExtractorError("The invalid url", expected=True)
        return data

    def _extract_program(self, info, program_corner_id):
        id = program_corner_id + "_" + info.get("headline_id")
        file = info.get("file_list")[0]
        formats = self._extract_m3u8_formats(file.get("file_name", None), id, "m4a", entry_protocol="m3u8_native", m3u8_id="hls")
        self._sort_formats(formats)
        return {
            "id": id,
            "title": file.get("file_title"),
            "formats": formats,
            "timestamp": parse_iso8601(file.get("close_time")),
        }


class NhkRadioIE(NhkRadioBase):
    _VALID_URL = r"https?://www\.nhk\.or\.jp/radio/player/ondemand\.html\?p=(?P<program_id>\d+)_(?P<corner_id>\d+)_(?P<headline_id>\d+)"

    _TESTS = [
        {
            "url": "https://www.nhk.or.jp/radio/player/ondemand.html?p=4812_01_2898188",
            "info_dict": {
                "id": "4812_01_2898188",
                "ext": "m4a",
                "title": "世界へ発信！ニュースで英語術　＃２０９▽“首相長男から接待”　総務省１１人を処分",
                "upload_date": str,
                "timestamp": int,
            },
        },
        {
            "url": "https://www.nhk.or.jp/radio/player/ondemand.html?p=0444_01_2890944",
            "info_dict": {
                "ext": "m4a",
                "id": "0444_01_2890944",
                "title": "歌謡スクランブル　春色コレクション（３）　▽尾崎亜美",
                "upload_date": str,
                "timestamp": int,
            },
        },
    ]

    def _real_extract(self, url):
        program_id, corner_id, headline_id = re.match(self._VALID_URL, url).groups()
        program_corner_id = program_id + "_" + corner_id
        data = self._download_json(
            "https://www.nhk.or.jp/radioondemand/json/"
            + program_id
            + "/bangumi_"
            + program_corner_id
            + ".json",
            program_corner_id,
        )
        for detail in data["main"]["detail_list"]:
            if headline_id == detail.get("headline_id"):
                return self._extract_program(detail, program_corner_id)
        raise ExtractorError("The program not found", expected=True)


class NhkRadioProgramIE(NhkRadioBase):
    _VALID_URL = r"https?://www\.nhk\.or\.jp/radio/ondemand/detail\.html\?p=(?P<program_id>\d+)_(?P<corner_id>\d+)"

    _TESTS = [
        {
            "url": "https://www.nhk.or.jp/radio/ondemand/detail.html?p=0164_01",
            "info_dict": {"title": "青春アドベンチャー", "id": "0164_01"},
            "playlist_mincount": 5,
        },
        {
            "url": "https://www.nhk.or.jp/radio/ondemand/detail.html?p=0455_01",
            "info_dict": {"id": "0455_01", "title": "弾き語りフォーユー"},
            "playlist_mincount": 5,
        },
    ]

    def _real_extract(self, url):
        program_id, corner_id = re.match(self._VALID_URL, url).groups()
        data = self._get_json_meta(program_id, corner_id)
        entries = []
        for detail in data["main"]["detail_list"]:
            entries.append(self._extract_program(detail, program_id + "_" + corner_id))
        return self.playlist_result(
            entries, program_id + "_" + corner_id, data["main"]["program_name"]
        )
