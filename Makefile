all: compile exe readme man-page bash-completion update-latest

update-latest:
	./youtube-dl --version > LATEST_VERSION

readme:
	@options=$$(COLUMNS=80 ./youtube-dl --help | sed -e '1,/.*General Options.*/ d' -e 's/^\W\{2\}\(\w\)/## \1/') && \
		header=$$(sed -e '/.*# OPTIONS/,$$ d' README.md) && \
		footer=$$(sed -e '1,/.*# FAQ/ d' README.md) && \
		echo "$${header}" > README.md && \
		echo >> README.md && \
		echo '# OPTIONS' >> README.md && \
		echo "$${options}" >> README.md&& \
		echo >> README.md && \
		echo '# FAQ' >> README.md && \
		echo "$${footer}" >> README.md

man-page:
	pandoc -s -w man README.md -o youtube-dl.1

bash-completion:
	@options=`egrep -o '(--[a-z-]+) ' README.md | sort -u | xargs echo` && \
		content=`sed "s/opts=\"[^\"]*\"/opts=\"$${options}\"/g" youtube-dl.bash-completion` && \
		echo "$${content}" > youtube-dl.bash-completion

compile:
	zip --quiet --junk-paths youtube-dl youtube_dl/*.py
	echo '#!/usr/bin/env python' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip

exe:
	bash devscripts/wine-py2exe.sh build_exe.py

install:
	install -m 755 --owner root --group root youtube-dl /usr/local/bin/
	install -m 644 --owner root --group root youtube-dl.1 /usr/local/man/man1
	install -m 644 --owner root --group root youtube-dl.bash-completion /etc/bash_completion.d/youtube-dl

release:
	@if [ -z "$$version" ]; then echo 'ERROR: specify version number like this: make release version=1994.09.06'; exit 1; fi
	@if [ ! -z "`git tag | grep "$$version"`" ]; then echo 'ERROR: version already present'; exit 1; fi
	@if [ ! -z "`git status --porcelain`" ]; then echo 'ERROR: the working directory is not clean; commit or stash changes'; exit 1; fi
	@sed -i "s/__version__ = '.*'/__version__ = '$$version'/" youtube_dl/__init__.py
	make all
	git add -A
	git commit -m "release $$version"
	git tag -m "Release $$version" "$$version"

.PHONY: all update-latest readme man-page bash-completion compile exe install release
