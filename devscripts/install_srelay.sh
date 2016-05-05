#!/bin/bash

mkdir -p tmp && cd tmp
wget -N http://downloads.sourceforge.net/project/socks-relay/socks-relay/srelay-0.4.8/srelay-0.4.8b6.tar.gz
tar zxvf srelay-0.4.8b6.tar.gz
cd srelay-0.4.8b6
./configure
make
