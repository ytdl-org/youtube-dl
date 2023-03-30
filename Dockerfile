# Start from the yb_ubuntu:18.04 base image
FROM yourbase/yb_ubuntu:18.04


# Update the package manager and install Python 3.9
RUN apt-get update && \
    apt-get install -y python3.10 && \
    apt-get install -y git

RUN which python3

# Set the default Python version to 3.10
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1


# Download the get-pip.py script and install pip
RUN curl https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py
RUN python3 get-pip.py

# Verify that pip is installed
RUN pip --version

RUN pip install yourbase

RUN pip install nose

RUN pip install pytest

ENV YTDL_TEST_SET core

# Copy the repository into the container
COPY . /app

# Set the working directory to the app directory
WORKDIR /app

# Install any dependencies required by the repository using pip
# RUN python3 -m pip install -r requirements.txt

# Run any necessary setup commands for the repository
CMD ["./devscripts/test-yourbase.sh"]