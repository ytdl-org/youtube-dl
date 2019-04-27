FROM alpine:3.9 as builder_pandoc
RUN apk update && \
    apk add cabal \ 
            zlib-dev \
            wget \
            ghc \
            musl-dev && \
    cabal update && \
    cabal install --upgrade-dependencies --enable-per-component -j --force-reinstalls pandoc

FROM alpine:3.9 as builder_ytdl
COPY --from=builder_pandoc /root/.cabal /root/.cabal
RUN apk update && \
    apk add ffmpeg \
            rtmpdump \
            mplayer \
            mpv \
            python3 \
            git \
            make \
            zip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /root/.cabal/bin/pandoc /usr/local/bin/pandoc && \
    git clone https://github.com/ytdl-org/youtube-dl.git && \
    cd /youtube-dl && \
    make -j && \
    make install

FROM alpine:3.9 as final
COPY --from=builder_ytdl /usr/local/bin/youtube-dl /usr/local/bin/youtube-dl
COPY --from=builder_ytdl /usr/local/man/man1/youtube-dl.1 /usr/local/man/man1/youtube-dl.1
RUN apk update && \
    apk add ffmpeg \
            rtmpdump \
            mplayer \
            mpv \
            python3 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    youtube-dl --version && \
    rm -rf /var/cache/apk/*

COPY init /init
WORKDIR /home/dockeruser
ENTRYPOINT ["/init"]

