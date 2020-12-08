from ubuntu as builder
copy . /src
workdir /src
run apt-get update ; \
    apt-get install -y \
        make \
        zip \
        python3 \
        python-is-python3 \
        pandoc
run make
from ubuntu
copy --from=builder /src/youtube-dl /youtube-dl
run apt-get update ; \
    apt-get install -y \
        ca-certificates \
        ffmpeg \
        python-is-python3 \
        python3 
workdir /data
entrypoint ["/youtube-dl"]
