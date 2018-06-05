#!/usr/bin/env python

import os

script_name = "paf-baseband2power.py"
conf_fname  = "paf-baseband2power.conf"
dir_name    = "/beegfs/DENG/docker/"
gpu         = 1
visiblegpu  = 1
nvprof      = 0
memcheck    = 0
dfname      = "2018-04-17-19:22:11.56868_0000000000000000.000000.dada"

if nvprof == 1:
    com_line = "nvprof --profile-child-processes ./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:s}".format(script_name, conf_fname, dir_name, gpu, str(visiblegpu), memcheck, dfname)
else:
    com_line = "./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:s}".format(script_name, conf_fname, dir_name, gpu, str(visiblegpu), memcheck, dfname)

print com_line
os.system(com_line)
