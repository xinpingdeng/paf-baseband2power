#!/usr/bin/env python

import os, argparse

# ./run_outside.py -a /beegfs/DENG/JUNE/ -b 100 -c 1 -d 9

# Read in command line arguments
parser = argparse.ArgumentParser(description='Convert baseband data into power')
parser.add_argument('-a', '--ddir', type=str, nargs='+',
                    help='Directory for data recording')
parser.add_argument('-b', '--length', type=float, nargs='+',
                    help='Observing length in seconds')
parser.add_argument('-c', '--numa', type=int, nargs='+',
                    help='On which numa node we do the work, 0 or 1')
parser.add_argument('-d', '--nbeam', type=int, nargs='+',
                    help='Number of beams.')

args       = parser.parse_args()
ddir       = args.ddir[0]
length     = args.length[0]
nbeam      = args.nbeam[0]
numa       = args.numa[0]

#ddir       = "/beegfs/DENG/JUNE/"
#length     = 100
#nbeam      = 9
#numa       = 1

hdir       = "/home/pulsar"
memsize    = 80000000000
uid        = 50000
gid        = 50000
gpu        = numa
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
