FROM alpine:3.12 AS builder
RUN apk add make zip
WORKDIR /src
COPY . .
RUN make youtube-dl

FROM alpine:3.12
RUN apk --no-cache add python3 ffmpeg \
  && ln -s /usr/bin/python3 /usr/bin/python
COPY --from=builder /src/youtube-dl /usr/local/bin/
WORKDIR /downloads
USER guest
ENTRYPOINT ["youtube-dl"]
CMD ["--help"]
