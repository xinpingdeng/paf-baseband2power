# Copyright (C) 2016 by Ewan Barr
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

FROM xinpingdeng/paf-base
MAINTAINER Xinping Deng "xinping.deng@gmail.com"

# Use pulsar
USER pulsar
WORKDIR /home/pulsar/xinpingdeng/paf-baseband2power

RUN git clone https://github.com/xinpingdeng/paf-baseband2power.git && \
    git checkout dev && \
    git config user.name "xinpingdeng" && \
    git config user.email "xinping.deng@gmail.com" && \
    ./rebuild.py 0 

ENTRYPOINT ["./run_outside.py"]    