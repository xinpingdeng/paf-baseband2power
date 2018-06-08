#!/usr/bin/env python

import os

hdir       = "/home/pulsar"
ddir       = "/beegfs/DENG/JUNE/"
memsize    = 80000000000
uid        = 50000
gid        = 50000
numa       = 1
gpu        = numa
length     = 100
nbeam      = 9
dname      = "paf-baseband2power"
conf_fname = "paf-baseband2power-stream.conf"

visiblegpu  = 1
memcheck    = 0

dvolume = '{:s}:{:s}'.format(ddir, ddir)
hvolume = '{:s}:{:s}'.format(hdir, hdir)

#com_line = "docker run -it --rm --runtime=nvidia -e DISPLAY --net=host -v {:s} -v {:s} -u {:d}:{:d} -e NVIDIA_VISIBLE_DEVICES={:s} -e NVIDIA_DRIVER_CAPABILITIES=all --ulimit memlock={:d} --name {:s} {:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:f} -g {:d}".format(dvolume, hvolume, uid, gid, str(gpu), memsize, dname, dname, conf_fname, ddir, numa, str(visiblegpu), memcheck, length, nbeam)
com_line = "docker run -it --rm --runtime=nvidia -e DISPLAY --net=host -v {:s} -u {:d}:{:d} -e NVIDIA_VISIBLE_DEVICES={:s} -e NVIDIA_DRIVER_CAPABILITIES=all --ulimit memlock={:d} --name {:s} {:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:f} -g {:d}".format(dvolume, uid, gid, str(gpu), memsize, dname, dname, conf_fname, ddir, numa, str(visiblegpu), memcheck, length, nbeam)
print com_line
os.system(com_line)
