FROM gliderlabs/alpine:3.2

RUN apk --update add ca-certificates python

ADD https://yt-dl.org/latest/youtube-dl /usr/local/bin/youtube-dl

RUN chmod a+rx /usr/local/bin/youtube-dl