#   -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pybuilder.core import task, dependents, depends, use_plugin, init
from enum import Enum
import glob
import shutil
import sys
import os
import subprocess

use_plugin("python.core")
# use_plugin("python.unittest")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("exec")

name = "youtube-dl"
default_task = ["clean", "build"]
version = "0.0.0"

OS = Enum('OS', ['Linux', 'MacOS', 'Windows'])


@init
def set_properties(project):
    project.set_property("dir_source_main_python", "youtube_dl")
    project.set_property("dir_source_unittest_python", "test")
    project.set_property("dir_source_main_scripts", "devscripts")
    # project.set_property("unittest_module_glob", "test*")
    project.set_property('coverage_break_build', False)
    sys.path.append("./youtube_dl")
    from version import __version__
    project.version = __version__
    type = OS.Linux
    if sys.platform == "linux" or sys.platform == "linux2":
        type = OS.Linux
    elif sys.platform == "darwin":
        type = OS.MacOS
    elif sys.platform == "win32":
        type = OS.Windows
    project.os = type


def delete(logger, path):
    if (os.path.exists(path)):
        logger.info("Deleting: " + path)
        if (os.path.isfile(path)):
            os.remove(path)
        elif (os.path.isdir(path)):
            shutil.rmtree(path)


@task
def clean(logger, project):
    delete_patterns = [
        "*/__pycache__",
        "*/testdata",
        "*.pyc",
        "*.class",
        "*.dump",
        "*.part*",
        "*.ytdl",
        "*.info.json",
        "*.mp4",
        "*.m4a",
        "*.flv",
        "*.mp3",
        "*.avi",
        "*.mkv",
        "*.webm",
        "*.3gp",
        "*.wav",
        "*.ape",
        "*.swf",
        "*.jpg",
        "*.png",
    ]

    for pat in delete_patterns:
        for file in glob.glob(pat):
            delete(logger, file)

    delete_files = [
        'youtube-dl.1.temp.md',
        'youtube-dl.1',
        'youtube-dl.bash-completion',
        'README.txt',
        'MANIFEST',
        'build/',
        'dist/',
        '.coverage',
        'cover/',
        'youtube-dl.tar.gz',
        'youtube-dl.zsh',
        'youtube-dl.fish',
        'youtube_dl/extractor/lazy_extractors.py',
        'CONTRIBUTING.md.tmp',
        'youtube-dl',
        'youtube-dl.exe'
    ]

    for file in delete_files:
        delete(logger, file)


@task
# build for the current operating system
def build(logger, project):
    if (project.os == OS.Linux or project.os == OS.MacOS):
        buildUnix(logger, project)
    elif project.os == OS.Windows:
        buildWin32(logger, project)
    else:
        logger.error("Operating system detection failed, please manually select an OS to build for!")
        logger.error("$ pyb buildUnix or $ pyb buildWin32")


def mkdir_p(path):
    try:
        return os.mkdir(path)
    except FileExistsError:
        pass


@task
@dependents("installUnix")
def buildUnix(logger, project):
    logger.info(project.version)
    mkdir_p("zip")
    source_dirs = [
        "youtube_dl", "youtube_dl/downloader", "youtube_dl/extractor", "youtube_dl/postprocessor"
    ]
    for dir in source_dirs:
        mkdir_p("zip/" + dir)
        subprocess.run("cp -pPr " + dir + "/*.py zip/" + dir + "/", shell=True)
    subprocess.run("touch -t 200001010101 zip/youtube_dl/*.py zip/youtube_dl/*/*.py", shell=True)
    subprocess.run("mv zip/youtube_dl/__main__.py zip/", shell=True)
    subprocess.run("cd zip ; zip -q ../youtube-dl youtube_dl/*.py youtube_dl/*/*.py __main__.py", shell=True)
    subprocess.run("rm -rf zip", shell=True)
    subprocess.run("echo '#!/usr/bin/env python' > youtube-dl ; cat youtube-dl.zip >> youtube-dl ; rm  youtube-dl.zip; chmod a+x youtube-dl", shell=True)


@task
@depends("buildUnix")
def installUnix(logger, project):
    PREFIX = "/usr/local"
    BINDIR = f"{PREFIX}/bin"
    MANDIR = f"{PREFIX}/man"
    SHAREDIR = f"{PREFIX}/share"
    # SYSCONFDIR = f"$(shell if [ $(PREFIX) = /usr -o $(PREFIX) = /usr/local ]; then echo /etc; else echo $(PREFIX)/etc; fi)
    SYSCONFDIR = ""

    DESTDIR = ""

    subprocess.run(f"install -d {DESTDIR}{BINDIR}\
                    install -m 755 youtube-dl {DESTDIR}{BINDIR}\
                    install -d {DESTDIR}{MANDIR}/man1\
                    install -m 644 youtube-dl.1 {DESTDIR}{MANDIR}/man1\
                    install -d {DESTDIR}{SYSCONFDIR}/bash_completion.d\
                    install -m 644 youtube-dl.bash-completion {DESTDIR}{SYSCONFDIR}/bash_completion.d/youtube-dl\
                    install -d {DESTDIR}{SHAREDIR}/zsh/site-functions\
                    install -m 644 youtube-dl.zsh {DESTDIR}{SHAREDIR}/zsh/site-functions/_youtube-dl\
                    install -d {DESTDIR}{SYSCONFDIR}/fish/completions\
                    install -m 644 youtube-dl.fish {DESTDIR}{SYSCONFDIR}/fish/completions/youtube-dl.fish",
                   shell=True)


@task
def buildWin32(logger, project):
    subprocess.run("python -m setup.py py2exe")


@task
def offlinetest(logger, project):
    res = subprocess.run("python -m nose --verbose test \
                   --exclude test_age_restriction.py \
                           --exclude test_download.py \
                   --exclude test_iqiyi_sdk_interpreter.py \
                       --exclude test_socks.py \
                           --exclude test_subtitles.py \
                           --exclude test_write_annotations.py \
                           --exclude test_youtube_lists.py \
                           --exclude test_youtube_signature.py",
                         shell=True)
    if (res.returncode != 0):
        sys.exit(res.returncode)


@task
def test(logger, project):
    res = subprocess.run("nosetests --with-coverage \
                    --cover-package=youtube_dl \
                    --cover-html \
                    --verbose \
                    --processes 4 test",
                         shell=True)
    if (res.returncode != 0):
        sys.exit(res.returncode)
