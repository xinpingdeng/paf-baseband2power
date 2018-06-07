#!/usr/bin/env python

# ./paf-baseband2power.py -a paf-baseband2power.conf -b /beegfs/DENG/docker/ -c 0 -d 0 -e 0 -f 10

import os, time, threading, ConfigParser, argparse, socket, json, struct, sys

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

# Read in command line arguments
parser = argparse.ArgumentParser(description='Convert baseband data into power')
parser.add_argument('-a', '--cfname', type=str, nargs='+',
                    help='The name of configuration file')
parser.add_argument('-b', '--directory', type=str, nargs='+',
                    help='In which directory we record the data and read configuration files and parameter files')
parser.add_argument('-c', '--numa', type=int, nargs='+',
                    help='On which numa node we do the work, 0 or 1')
parser.add_argument('-d', '--visiblegpu', type=str, nargs='+',
                    help='Visible GPU, the parameter is for the usage inside docker container.')
parser.add_argument('-e', '--memcheck', type=int, nargs='+',
                    help='To run cuda-memcheck or not.')
parser.add_argument('-f', '--length', type=float, nargs='+',
                    help='Length of data capture.')

## Get center frequency from multi cast
#multicast_group = '224.1.1.1'
#server_address = ('', 5007)
#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create the socket
#sock.bind(server_address) # Bind to the server address
#group = socket.inet_aton(multicast_group)
#mreq = struct.pack('4sL', group, socket.INADDR_ANY)
#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)  # Tell the operating system to add the socket to the multicast group on all interfaces.
##sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, mreq)  
#pkt, address = sock.recvfrom(1<<16)
#data = json.loads(pkt)#['beams_direction']#['beam01']
##sock.shutdown(socket.SHUT_RDWR)
#sock.close()
#freq = float(data['sky_frequency'])
#print "The centre frequency is {:.1f}MHz".format(freq)

args         = parser.parse_args()
cfname       = args.cfname[0]
numa         = args.numa[0]
nic          = numa + 1
visiblegpu   = args.visiblegpu[0]
directory    = args.directory[0]
memcheck     = args.memcheck[0]
length       = args.length[0]

hdr  = 0
freq = 1340.5

if(args.visiblegpu[0]==''):
    multi_gpu = 1;
if(args.visiblegpu[0]=='all'):
    multi_gpu = 1;
else:
    multi_gpu = 0;
    
# Play with configuration file
Config = ConfigParser.ConfigParser()
Config.read(cfname)

# Basic configuration
nsamp_df     = int(ConfigSectionMap("BasicConf")['nsamp_df'])
npol_samp    = int(ConfigSectionMap("BasicConf")['npol_samp'])
ndim_pol     = int(ConfigSectionMap("BasicConf")['ndim_pol'])
nchk_nic     = int(ConfigSectionMap("BasicConf")['nchk_nic'])
ncpu_numa    = int(ConfigSectionMap("BasicConf")['ncpu_numa'])

# Capture configuration
capture_ncpu    = int(ConfigSectionMap("CaptureConf")['ncpu'])
capture_ndf 	= int(ConfigSectionMap("CaptureConf")['ndf'])
capture_nbuf    = ConfigSectionMap("CaptureConf")['nblk']
capture_key     = ConfigSectionMap("CaptureConf")['key']
capture_key     = format(int("0x{:s}".format(capture_key), 0) + 2 * nic, 'x')
capture_kfname  = "{:s}_nic{:d}.key".format(ConfigSectionMap("CaptureConf")['kfname_prefix'], nic)
capture_efname  = ConfigSectionMap("CaptureConf")['efname']
capture_hfname  = ConfigSectionMap("CaptureConf")['hfname']
capture_nreader = ConfigSectionMap("CaptureConf")['nreader']
capture_sod     = ConfigSectionMap("CaptureConf")['sod']
capture_rbufsz  = capture_ndf *  nchk_nic * 7168

# baseband2power configuration
baseband2power_key        = ConfigSectionMap("Baseband2powerConf")['key']
baseband2power_kfname     = "{:s}.key".format(ConfigSectionMap("Baseband2powerConf")['kfname_prefix'])
baseband2power_key        = format(int("0x{:s}".format(baseband2power_key), 0), 'x')
baseband2power_sod        = int(ConfigSectionMap("Baseband2powerConf")['sod'])
baseband2power_nreader    = ConfigSectionMap("Baseband2powerConf")['nreader']
baseband2power_nbuf       = ConfigSectionMap("Baseband2powerConf")['nblk']
baseband2power_nchan      = int(ConfigSectionMap("Baseband2powerConf")['nchan'])
baseband2power_nbyte      = int(ConfigSectionMap("Baseband2powerConf")['nbyte'])
baseband2power_rbufsz     = baseband2power_nchan * baseband2power_nbyte
baseband2power_cpu        = ncpu_numa * numa + capture_ncpu

# Dbdisk configuration
dbdisk_cpu = ncpu_numa * numa + capture_ncpu + 1

def capture():
#    time.sleep(sleep_time)
    os.system("./paf_capture -a {:s} -b {:s} -c {:d} -d {:d} -e {:d} -f {:s} -g {:s} -i {:f} -j {:f} -k {:s}".format(capture_key, capture_sod, capture_ndf, hdr, nic, capture_hfname, capture_efname, freq, length, directory))

def baseband2power():
    #if memcheck:
    #    print ('taskset -c {:d} cuda-memcheck ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, gpu, capture_ndf, baseband2power_nchan, baseband2power_sod))
    #    os.system('taskset -c {:d} cuda-memcheck ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, gpu, capture_ndf, baseband2power_nchan, baseband2power_sod))
    #else:
    #    print ('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, gpu, capture_ndf, baseband2power_nchan, baseband2power_sod))
    #    os.system('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, gpu, capture_ndf, baseband2power_nchan, baseband2power_sod))
    if multi_gpu:
        print ('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, numa, capture_ndf, baseband2power_nchan, baseband2power_sod))
        os.system('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, numa, capture_ndf, baseband2power_nchan, baseband2power_sod))
    else:
        print ('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, 0, capture_ndf, baseband2power_nchan, baseband2power_sod))
        os.system('taskset -c {:d} ./paf_baseband2power -a {:s} -b {:s} -c {:s} -d {:d} -e {:d} -f {:d} -g {:d}'.format(baseband2power_cpu, capture_key, baseband2power_key, directory, 0, capture_ndf, baseband2power_nchan, baseband2power_sod))
            
def dbdisk():
    print ('dada_dbdisk -b {:d} -k {:s} -D {:s} -W -s -d'.format(dbdisk_cpu, baseband2power_key, directory))
    os.system('dada_dbdisk -b {:d} -k {:s} -D {:s} -W -s -d'.format(dbdisk_cpu, baseband2power_key, directory))

def main():
    # Create key files
    # and destroy share memory at the last time
    # this will save prepare time for the pipeline as well
    capture_key_file = open(capture_kfname, "w")
    capture_key_file.writelines("DADA INFO:\n")
    capture_key_file.writelines("key {:s}\n".format(capture_key))
    capture_key_file.close()

    # Create key files
    # and destroy share memory at the last time
    # this will save prepare time for the pipeline as well
    baseband2power_key_file = open(baseband2power_kfname, "w")
    baseband2power_key_file.writelines("DADA INFO:\n")
    baseband2power_key_file.writelines("key {:s}\n".format(baseband2power_key))
    baseband2power_key_file.close()

    os.system("dada_db -l -p -k {:s} -b {:d} -n {:s} -r {:s}".format(capture_key, capture_rbufsz, capture_nbuf, capture_nreader))
    os.system("dada_db -l -p -k {:s} -b {:d} -n {:s} -r {:s}".format(baseband2power_key, baseband2power_rbufsz, baseband2power_nbuf, baseband2power_nreader))
    
    t_capture  = threading.Thread(target = capture)
    t_baseband2power = threading.Thread(target = baseband2power)
    t_dbdisk    = threading.Thread(target = dbdisk)
    
    t_capture.start()
    t_baseband2power.start()
    t_dbdisk.start()
    
    t_capture.join()
    t_baseband2power.join()
    t_dbdisk.join()

    os.system("dada_db -d -k {:s}".format(capture_key))
    os.system("dada_db -d -k {:s}".format(baseband2power_key))
    
if __name__ == "__main__":
    main()
