all: youtube-dl README.md README.txt youtube-dl.1 youtube-dl.bash-completion

clean:
	rm -rf youtube-dl.1 youtube-dl.bash-completion README.txt MANIFEST build/ dist/ .coverage cover/ youtube-dl.tar.gz

cleanall: clean
	rm -f youtube-dl youtube-dl.exe

PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/man
PYTHON=/usr/bin/env python

# set SYSCONFDIR to /etc if PREFIX=/usr or PREFIX=/usr/local
ifeq ($(PREFIX),/usr)
	SYSCONFDIR=/etc
else
	ifeq ($(PREFIX),/usr/local)
		SYSCONFDIR=/etc
	else
		SYSCONFDIR=$(PREFIX)/etc
	endif
endif

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

tar: youtube-dl.tar.gz

.PHONY: all clean install test tar bash-completion pypi-files

pypi-files: youtube-dl.bash-completion README.txt youtube-dl.1

youtube-dl: youtube_dl/*.py youtube_dl/*/*.py
	zip --quiet youtube-dl youtube_dl/*.py youtube_dl/*/*.py
	zip --quiet --junk-paths youtube-dl youtube_dl/__main__.py
	echo '#!$(PYTHON)' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip
	chmod a+x youtube-dl

README.md: youtube_dl/*.py youtube_dl/*/*.py
	COLUMNS=80 python -m youtube_dl --help | python devscripts/make_readme.py

README.txt: README.md
	pandoc -f markdown -t plain README.md -o README.txt

youtube-dl.1: README.md
	pandoc -s -f markdown -t man README.md -o youtube-dl.1

youtube-dl.bash-completion: youtube_dl/*.py youtube_dl/*/*.py devscripts/bash-completion.in
	python devscripts/bash-completion.py

bash-completion: youtube-dl.bash-completion

youtube-dl.tar.gz: youtube-dl README.md README.txt youtube-dl.1 youtube-dl.bash-completion
	@tar -czf youtube-dl.tar.gz --transform "s|^|youtube-dl/|" --owner 0 --group 0 \
		--exclude '*.DS_Store' \
		--exclude '*.kate-swp' \
		--exclude '*.pyc' \
		--exclude '*.pyo' \
		--exclude '*~' \
		--exclude '__pycache' \
		--exclude '.git' \
		--exclude 'testdata' \
		-- \
		bin devscripts test youtube_dl \
		CHANGELOG LICENSE README.md README.txt \
		Makefile MANIFEST.in youtube-dl.1 youtube-dl.bash-completion setup.py \
		youtube-dl
