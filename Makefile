all: youtube-dl README.md youtube-dl.1 youtube-dl.bash-completion LATEST_VERSION
# TODO: re-add youtube-dl.exe, and make sure it's 1. safe and 2. doesn't need sudo

clean:
	rm -f youtube-dl youtube-dl.exe youtube-dl.1 LATEST_VERSION

PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/man
SYSCONFDIR=/etc

install: youtube-dl youtube-dl.1 youtube-dl.bash-completion
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 youtube-dl $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(MANDIR)/man1
	install -m 644 youtube-dl.1 $(DESTDIR)$(MANDIR)/man1
	install -d $(DESTDIR)$(SYSCONFDIR)/bash_completion.d
	install -m 644 youtube-dl.bash-completion $(DESTDIR)$(SYSCONFDIR)/bash_completion.d/youtube-dl

test:
	nosetests2 --nocapture test

.PHONY: all clean install test README.md youtube-dl.bash-completion
# TODO un-phony README.md and youtube-dl.bash_completion by reading from .in files and generating from them

youtube-dl: youtube_dl/*.py
	zip --quiet youtube-dl youtube_dl/*.py
	zip --quiet --junk-paths youtube-dl youtube_dl/__main__.py
	echo '#!/usr/bin/env python' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip
	chmod a+x youtube-dl

youtube-dl.exe: youtube_dl/*.py
	bash devscripts/wine-py2exe.sh build_exe.py

README.md: youtube_dl/*.py
	@options=$$(COLUMNS=80 python -m youtube_dl --help | sed -e '1,/.*General Options.*/ d' -e 's/^\W\{2\}\(\w\)/## \1/') && \
		header=$$(sed -e '/.*# OPTIONS/,$$ d' README.md) && \
		footer=$$(sed -e '1,/.*# CONFIGURATION/ d' README.md) && \
		echo "$${header}" > README.md && \
		echo >> README.md && \
		echo '# OPTIONS' >> README.md && \
		echo "$${options}" >> README.md&& \
		echo >> README.md && \
		echo '# CONFIGURATION' >> README.md && \
		echo "$${footer}" >> README.md

youtube-dl.1: README.md
	pandoc -s -w man README.md -o youtube-dl.1

youtube-dl.bash-completion: README.md
	@options=`egrep -o '(--[a-z-]+) ' README.md | sort -u | xargs echo` && \
		content=`sed "s/opts=\"[^\"]*\"/opts=\"$${options}\"/g" youtube-dl.bash-completion` && \
		echo "$${content}" > youtube-dl.bash-completion

LATEST_VERSION: youtube_dl/__init__.py
	python -m youtube_dl --version > LATEST_VERSION
