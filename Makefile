default: update

update: compile update-readme update-latest

update-latest:
	./youtube-dl.dev --version > LATEST_VERSION

update-readme:
	@options=$$(COLUMNS=80 ./youtube-dl.dev --help | sed -e '1,/.*General Options.*/ d' -e 's/^\W\{2\}\(\w\)/### \1/') && \
		header=$$(sed -e '/.*## OPTIONS/,$$ d' README.md) && \
		footer=$$(sed -e '1,/.*## FAQ/ d' README.md) && \
		echo "$${header}" > README.md && \
		echo >> README.md && \
		echo '## OPTIONS' >> README.md && \
		echo "$${options}" >> README.md&& \
		echo >> README.md && \
		echo '## FAQ' >> README.md && \
		echo "$${footer}" >> README.md

compile:
	zip --quiet --junk-paths youtube-dl youtube_dl/*.py
	echo '#!/usr/bin/env python' > youtube-dl
	cat youtube-dl.zip >> youtube-dl
	rm youtube-dl.zip

.PHONY: default compile update update-latest update-readme
