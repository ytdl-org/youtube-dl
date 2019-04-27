#!/bin/bash -x

# Build "latest"
docker build . -t ytdl-org/youtube-dl:latest 
build_exit=$?


# Get version of latest container
# Repeat as running straight after the build can give a 'bad interpreter: Text file busy' error
n=0
until [ $n -ge 5 ]
do
    build_version=$(docker run --rm -ti ytdl-org/youtube-dl --version) 
    if [ $? -eq 0 ]; then
        build_version=$(echo $build_version | sed 's/\r$//')
        break
    fi
    n=$[$n+1]
    sleep 15
done
if [ $n -ge 5 ]; then
    echo "Failed when trying to get youtube-dl version in latest container :("
    exit 1
fi

# If the build was successful, then we can tag with current version
if [ $build_exit -eq 0 ]; then
    docker tag ytdl-org/youtube-dl:latest ytdl-org/youtube-dl:$build_version
    tag_exit=$?
fi

if [ $build_exit -eq 0 ]; then
    if [ $tag_exit -eq 0 ]; then
        # If building and tagging was successful, then push
        docker push ytdl-org/youtube-dl:latest
        docker push ytdl-org/youtube-dl:$build_version
        exit 0
    fi
fi

echo "Something went wrong..."
exit 1
