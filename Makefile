all: youtube-dl README.md youtube-dl.1 youtube-dl.bash-completion LATEST_VERSION
# TODO: re-add youtube-dl.exe, and make sure it's 1. safe and 2. doesn't need sudo

clean:
	rm -f youtube-dl youtube-dl.exe youtube-dl.1 LATEST_VERSION

PREFIX=/usr/local
install: youtube-dl youtube-dl.1 youtube-dl.bash-completion
	install -m 755 --owner root --group root youtube-dl $(PREFIX)/bin/
	install -m 644 --owner root --group root youtube-dl.1 $(PREFIX)/man/man1
	install -m 644 --owner root --group root youtube-dl.bash-completion /etc/bash_completion.d/youtube-dl

.PHONY: all clean install README.md youtube-dl.bash-completion
# TODO un-phony README.md and youtube-dl.bash_completion by reading from .in files and generating from them

youtube-dl: youtube_dl/*.py
	zip --quiet --junk-paths youtube-dl youtube_dl/*.py
	echo '#!/usr/bin/env python' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip
	chmod a+x youtube-dl

youtube-dl.exe: youtube_dl/*.py
	bash devscripts/wine-py2exe.sh build_exe.py

README.md: youtube_dl/*.py
	@options=$$(COLUMNS=80 python -m youtube_dl --help | sed -e '1,/.*General Options.*/ d' -e 's/^\W\{2\}\(\w\)/## \1/') && \
		header=$$(sed -e '/.*# OPTIONS/,$$ d' README.md) && \
		footer=$$(sed -e '1,/.*# FAQ/ d' README.md) && \
		echo "$${header}" > README.md && \
		echo >> README.md && \
		echo '# OPTIONS' >> README.md && \
		echo "$${options}" >> README.md&& \
		echo >> README.md && \
		echo '# FAQ' >> README.md && \
		echo "$${footer}" >> README.md

youtube-dl.1: README.md
	pandoc -s -w man README.md -o youtube-dl.1

youtube-dl.bash-completion: README.md
	@options=`egrep -o '(--[a-z-]+) ' README.md | sort -u | xargs echo` && \
		content=`sed "s/opts=\"[^\"]*\"/opts=\"$${options}\"/g" youtube-dl.bash-completion` && \
		echo "$${content}" > youtube-dl.bash-completion

LATEST_VERSION: youtube_dl/__init__.py
	python -m youtube_dl --version > LATEST_VERSION

test:
	nosetests2 test

.PHONY: default compile update update-latest update-readme test clean
