#!/usr/bin/env python

import subprocess
import sys
import threading
import time
import socket
import os

def run_outside(ddir, length, nbeam, numa):
    hdir       = "/home/pulsar"
    memsize    = 100000000000
    uid        = 50000
    gid        = 50000
    gpu        = numa
    dname      = "paf-baseband2power"
    conf_fname = "paf-baseband2power-stream.conf"
    visiblegpu  = 1
    memcheck    = 0
    
    node_id = int((socket.gethostname())[7])

    if node_id < 2:
        ddir = "{:s}/beam{:d}".format(ddir, node_id * 2 + numa)
    elif node_id > 2:
        ddir = "{:s}/beam{:d}".format(ddir, (node_id - 1) * 2 + numa)
    else:
        print "We do not use pacifix2 ..."
    if not os.path.exists(ddir):
        os.mkdir(ddir)

    dvolume = '{:s}:{:s}'.format(ddir, ddir)
    hvolume = '{:s}:{:s}'.format(hdir, hdir)

    com_line = "docker run -it --rm --runtime=nvidia -e DISPLAY --net=host -v {:s} -v {:s} -u {:d}:{:d} -e NVIDIA_VISIBLE_DEVICES={:s} -e NVIDIA_DRIVER_CAPABILITIES=all --ulimit memlock={:d} --name {:s}{:d} xinpingdeng/{:s} -a {:s} -b {:s} -c {:d} -d {:s} -e {:d} -f {:f} -g {:d}".format(dvolume, hvolume, uid, gid, str(gpu), memsize, dname, numa, dname, conf_fname, ddir, numa, str(visiblegpu), memcheck, length, nbeam)
    print com_line
    os.system(com_line)

def ssh(host, command):
    ssh = subprocess.Popen(["ssh", "%s" % host, command],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        print result
    
def main():
    nbeam = 9
    length = 100
    threads = []
    ddir = "/beegfs/DENG/JUNE"
    
    #for beam in range(0,4):
    #    numa = beam % 2
    #    node = beam / 2
    #    print numa, node
    #
    #    command = "run_outside({:s}, {:f}, {:d}, {:d})".format(ddir, length, nbeam, numa)
    #    host = "pacifix{:d}".format(node)
    #    print host, command
    #    threads.append(threading.Thread(target = ssh, args = (host, command,)))
    #
    #for beam in range(4, nbeam):
    #    numa = beam % 2
    #    node = beam / 2 + 1
    #    print numa, node
    #
    #    command = "run_outside({:s}, {:f}, {:d}, {:d})".format(ddir, length, nbeam, numa)
    #    host = "pacifix{:d}".format(node)
    #    print host, command
    #    threads.append(threading.Thread(target = ssh, args = (host, command,)))
    #
    #for beam in range(nbeam):
    #    threads[beam].start()
    #
    #for beam in range(nbeam):
    #    threads[beam].join()
    
    numa = 0
    node = 0
    #run_outside(ddir, length, nbeam, numa)
    command = "run_outside({:s}, {:f}, {:d}, {:d})".format(ddir, length, nbeam, numa)
    host = "pacifix{:d}".format(node)
    ssh(host, command)
    
if __name__ == "__main__":
    main()
