#!/usr/bin/env python

import os

#script_name = "paf-baseband2power-file.py"
#conf_fname  = "paf-baseband2power-file.conf"

script_name = "paf-baseband2power-stream.py"
conf_fname  = "paf-baseband2power-stream.conf"

dir_name    = "/beegfs/DENG/JUNE/"
numa        = 1
visiblegpu  = 1
nvprof      = 1
memcheck    = 0
length      = 100
#dfname      = "2018-04-17-19:22:11.56868_0000000000000000.000000.dada"

if nvprof == 1:
    com_line = "nvprof --profile-child-processes ./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:f}".format(script_name, conf_fname, dir_name, numa, str(visiblegpu), memcheck, length)
    #com_line = "nvprof --profile-child-processes ./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:s}".format(script_name, conf_fname, dir_name, numa, str(visiblegpu), memcheck, dfname)
else:
    com_line = "./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:f}".format(script_name, conf_fname, dir_name, numa, str(visiblegpu), memcheck, length)
    #com_line = "./{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:s}".format(script_name, conf_fname, dir_name, numa, str(visiblegpu), memcheck, dfname)

print com_line
os.system(com_line)
