all: youtube-dl README.md README.txt youtube-dl.1 youtube-dl.bash-completion

clean:
	rm -rf youtube-dl youtube-dl.exe youtube-dl.1 youtube-dl.bash-completion README.txt MANIFEST build/ dist/ .coverage cover/

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
	#nosetests --with-coverage --cover-package=youtube_dl --cover-html --verbose --processes 4 test
	nosetests --verbose test

.PHONY: all clean install test

youtube-dl: youtube_dl/*.py
	zip --quiet youtube-dl youtube_dl/*.py
	zip --quiet --junk-paths youtube-dl youtube_dl/__main__.py
	echo '#!/usr/bin/env python' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip
	chmod a+x youtube-dl

README.md: youtube_dl/*.py
	COLUMNS=80 python -m youtube_dl --help | python devscripts/make_readme.py

README.txt: README.md
	pandoc -f markdown -t plain README.md -o README.txt

youtube-dl.1: README.md
	pandoc -s -f markdown -t man README.md -o youtube-dl.1

youtube-dl.bash-completion: youtube_dl/*.py devscripts/bash-completion.in
	python devscripts/bash-completion.py

youtube-dl.tar.gz: all
	tar -cvzf youtube-dl.tar.gz -s "|^./|./youtube-dl/|" \
		--exclude-from=".tarignore" -- .
