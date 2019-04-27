# Builder container for pandoc, prerequisite for building youtube-dl
# (so build environment isn't in final container, to save space)
FROM alpine:3.9 as builder_pandoc
RUN apk update && \
    apk add cabal \ 
            zlib-dev \
            wget \
            ghc \
            musl-dev && \
    cabal update && \
    cabal install --upgrade-dependencies --enable-per-component -j --force-reinstalls pandoc

# Builder container for youtube-dl
# (so build environment isn't in final container, to save space)
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

# Final container
FROM alpine:3.9 as final
# Copy youtube-dl binary and manpage into container from builder container
COPY --from=builder_ytdl /usr/local/bin/youtube-dl /usr/local/bin/youtube-dl
COPY --from=builder_ytdl /usr/local/man/man1/youtube-dl.1 /usr/local/man/man1/youtube-dl.1
# Install & configure s6 overlay, then prerequisites for youtube-dl
RUN apk update && \
    apk add ffmpeg \
            rtmpdump \
            mplayer \
            mpv \
            python3 \
            bash && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    youtube-dl --version && \
    rm -rf /var/cache/apk/* /tmp/*
# Copy init script, set workdir & entrypoint
COPY init /init
WORKDIR /workdir
ENTRYPOINT ["/init"]
