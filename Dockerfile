# Copyright (C) 2016 by Ewan Barr
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

FROM nvidia/cuda:9.1-devel-ubuntu16.04

MAINTAINER Xinping Deng "xinping.deng@gmail.com"

# To get rid of "(TERM is not set, so the dialog frontend is not usable.)"
ARG DEBIAN_FRONTEND=noninteractive
# To use bash during build
SHELL ["/bin/bash", "-c"]          

# Create space for ssh daemon and update the system
RUN apt-get -y check && \
    apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install apt-utils software-properties-common && \
    apt-get -y update --fix-missing && \
    apt-get -y upgrade 

# Install dependencies
RUN apt-get --no-install-recommends -y install \
    build-essential \
    autoconf \
    autotools-dev \
    automake \
    autogen \
    libtool \
    libltdl-dev \
    pkg-config \ 
    cmake \
    csh \
    gcc \
    gfortran \
    wget \
    git \
    gawk \
    expect \	
    libcfitsio-dev \
    pgplot5 \
    swig2.0 \
    hwloc \
    python \
    python-dev \
    python-pip \
    libfftw3-dev \
    libx11-dev \
    libpng12-dev \
    libpnglite-dev \   
    libhdf5-dev \
    libxml2-dev \    
    libgsl-dev \
    && apt-get -y clean

# Install python packages
RUN pip install --upgrade pip -U && \
    hash -d pip && \
    pip install setuptools -U && \
    pip install wheel -U && \
    pip install numpy -U && \
    pip install scipy -U && \
    pip install matplotlib -U

# PGPLOT
ENV PGPLOT_DIR        /usr/lib/pgplot5
ENV PGPLOT_FONT       /usr/lib/pgplot5/grfont.dat
ENV PGPLOT_INCLUDES   /usr/include
ENV PGPLOT_BACKGROUND white
ENV PGPLOT_FOREGROUND black
ENV PGPLOT_DEV        /xs

# Define directory for source code, OSTYPE and installation directory
ENV SOURCE           /root
ENV PREFIX           /usr/local
ENV INSTALL_BIN      $PREFIX/bin
ENV INSTALL_INCLUDES $PREFIX/include
ENV INSTALL_LIB      $PREFIX/lib
ENV INSTALL_SHARE    $PREFIX/share
ENV OSTYPE           linux-gnu
ENV LOGIN_ARCH	     linux
ENV CUDA_DIR         /usr/local/cuda
ENV CUDA_HOME        $CUDA_DIR
ENV CUDA_LIB         $CUDA_DIR/lib64
ENV CUDA_INCLUDE     $CUDA_DIR/include
ENV C_INCLUDE_PATH   $C_INCLUDE_PATH:$INCLUDE_INCLUDE
ENV LD_LIBRARY_PATH  $LD_LIBRARY_PATH:$INSTALL_LIB

# Install psrcat
WORKDIR $SOURCE
RUN wget http://www.atnf.csiro.au/people/pulsar/psrcat/downloads/psrcat_pkg.tar.gz && \
    tar xvzf psrcat_pkg.tar.gz
WORKDIR $SOURCE/psrcat_tar
RUN /bin/bash makeit && \
    cp psrcat    $INSTALL_BIN && \
    cp *.h       $INSTALL_INCLUDES && \
    cp *.a       $INSTALL_LIB && \
    cp psrcat.db $INSTALL_SHARE
ENV PSRCAT_FILE  $INSTALL_SHARE/psrcat.db
WORKDIR $SOURCE
RUN rm -rf psrcat_tar psrcat_pkg.tar.gz

# Install PSRXML
WORKDIR $SOURCE
RUN git clone https://github.com/SixByNine/psrxml.git 
WORKDIR $SOURCE/psrxml
RUN autoreconf --install --warnings=none && \
    ./configure --prefix=$PREFIX && \
    make -j $(nproc) && \
    make install
WORKDIR $SOURCE
RUN rm -rf psrxml

# Install calceph
WORKDIR $SOURCE
RUN wget https://www.imcce.fr/content/medias/recherche/equipes/asd/calceph/calceph-3.1.0.tar.gz && \
    tar xvzf calceph-3.1.0.tar.gz
WORKDIR $SOURCE/calceph-3.1.0
RUN ./configure --enable-shared CFLAGS=-fPIC FFLAGS=-fPIC --prefix=$PREFIX && \
    make -j $(nproc) && \
    make install
WORKDIR $SOURCE
RUN rm -rf calceph-3.1.0 calceph-3.1.0.tar.gz

# Install tempo2
WORKDIR $SOURCE
ENV TEMPO2 $INSTALL_SHARE
RUN git clone https://bitbucket.org/psrsoft/tempo2.git 
WORKDIR $SOURCE/tempo2
RUN cp -r T2runtime/* $TEMPO2 && \
    ./bootstrap && \
    ./configure --prefix=$PREFIX --with-calceph=$INSTALL_LIB --enable-shared CFLAGS=-fPIC FFLAGS=-fPIC --enable-static --with-pic F77=gfortran --x-libraries=/usr/lib/x86_64-linux-gnu && \
    make -j $(nproc) && \
    make install && \
    make plugins-install -j $(nproc)
WORKDIR $SOURCE
RUN rm -rf tempo2

# Install psrchive
WORKDIR $SOURCE
RUN git clone git://git.code.sf.net/p/psrchive/code psrchive
WORKDIR $SOURCE/psrchive
RUN ./bootstrap && \
    ./configure --prefix=$PREFIX --enable-shared CFLAGS=-fPIC FFLAGS=-fPIC --enable-static F77=gfortran --x-libraries=/usr/lib/x86_64-linux-gnu --with-psrxml-dir=$PREFIX LDFLAGS="-L$INSTALL_LIB" LIBS="-lpsrxml -lxml2"  && \
    make -j $(nproc) && \
    make install
WORKDIR $SOURCE
RUN rm -rf psrchive

# Install psrdada
WORKDIR $SOURCE
RUN git clone https://github.com/xinpingdeng/psrdada.git
WORKDIR $SOURCE/psrdada
RUN ./bootstrap && \
    ./configure --prefix=$PREFIX --with-cuda-include-dir=$CUDA_INCLUDE --with-cuda-lib-dir=$CUDA_LIB && \
    make -j $(nproc)&& \
    make install
WORKDIR $SOURCE
RUN rm -rf psrdada

# Install dspsr
WORKDIR $SOURCE
RUN git clone git://git.code.sf.net/p/dspsr/code dspsr
WORKDIR $SOURCE/dspsr
RUN ./bootstrap && \
    echo " dummy fits sigproc dada" > backends.list && \
    ./configure --prefix=$PREFIX --with-cuda-lib-dir=$CUDA_LIB --with-cuda-include-dir=$CUDA_INCLUDE --x-libraries=/usr/lib/x86_64-linux-gnu CPPFLAGS="-I/usr/include/hdf5/serial" LDFLAGS="-L/usr/lib/x86_64-linux-gnu/hdf5/serial" LIBS="-lpgplot -lcpgplot -lpsrxml -lxml2" && \
    make -j $(nproc) && \
    make && \
    make install
WORKDIR $SOURCE
RUN rm -rf dspsr

# Create pulsar user, psr group and change the ownership
RUN groupadd -g 50000 psr && \
    useradd -u 50000 -g 50000 pulsar 

# More setup for psrchive on pulsar home directory
ARG HOME=/home/pulsar
RUN mkdir $HOME && \
    chown -R pulsar:psr $HOME
USER pulsar
#ENV HOME /home/pulsar
WORKDIR $HOME
RUN echo "Predictor::default = tempo2" >> .psrchive.cfg && \
    echo "Predictor::policy = default" >> .psrchive.cfg

# Back to root
USER root
WORKDIR /

# Use pulsar
USER pulsar
WORKDIR /home/pulsar/paf-baseband2power

RUN git clone https://github.com/xinpingdeng/paf-baseband2power.git && \
    git checkout dev && \
    git config user.name "xinpingdeng" && \
    git config user.email "xinping.deng@gmail.com" && \
    ./rebuild.py 0 && \

ENTRYPOINT ["./run.py"]    