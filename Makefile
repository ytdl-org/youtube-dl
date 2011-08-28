default: update

update: update-readme


update-readme:
	@options=$$(COLUMNS=80 ./youtube-dl --help | sed -e '1,/.*General Options.*/ d' -e 's/^\W\{2\}\(\w\)/### \1/') && \
		header=$$(sed -e '/.*## OPTIONS/,$$ d' README.md) && \
		footer=$$(sed -e '1,/.*## COPYRIGHT/ d' README.md) && \
		echo "$${header}" > README.md && \
		echo -e '\n## OPTIONS' >> README.md && \
		echo "$${options}" >> README.md&& \
		echo -e '\n## COPYRIGHT' >> README.md && \
		echo "$${footer}" >> README.md



.PHONY: default update update-readme
