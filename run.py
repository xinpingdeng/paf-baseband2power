#!/usr/bin/env python

import os

script_name = "paf-baseband2power.py"
conf_fname  = "paf-baseband2power.conf"
dir_name    = "/beegfs/DENG/docker/"
gpu         = 1
visiblegpu  = 1
nvprof      = 1
memcheck    = 0

if nvprof == 1:
    com_line = "nvprof --profile-child-processes ./{:s} -a {:s} -b {:s} -c {:s} -d {:d} -e {:s} -f {:s} -g {:d}".format(script_name, conf_fname, dir_name, gpu, str(visiblegpu), memcheck)
else:
    com_line = "./{:s} -a {:s} -b {:s} -c {:s} -d {:d} -e {:s} -f {:s} -g {:d}".format(script_name, conf_fname, dir_name, gpu, str(visiblegpu), memcheck)

print com_line
os.system(com_line)
