#!/usr/bin/env python

# ./paf-baseband2power.py -a paf-baseband2power.conf -b /beegfs/DENG/JUNE/ -c 0 -d 0 -e 0 -f 10

import os, time, threading, ConfigParser, argparse, socket, json, struct, sys, datetime, pytz

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

def getDUTCDt(dt=None):
    """
    Get the DUTC value in seconds that applied at the given (datetime)
    timestamp.
    """
    dt = dt or utc_now()
    for i in LEAPSECONDS:
        if i[0] < dt:
            return i[2]
    # Different system used before then
    return 0

# Leap seconds definition, [UTC datetime, MJD, DUTC]
LEAPSECONDS = [
    [datetime.datetime(2017, 1, 1, tzinfo=pytz.utc), 57754, 37],
    [datetime.datetime(2015, 7, 1, tzinfo=pytz.utc), 57205, 36],
    [datetime.datetime(2012, 7, 1, tzinfo=pytz.utc), 56109, 35],
    [datetime.datetime(2009, 1, 1, tzinfo=pytz.utc), 54832, 34],
    [datetime.datetime(2006, 1, 1, tzinfo=pytz.utc), 53736, 33],
    [datetime.datetime(1999, 1, 1, tzinfo=pytz.utc), 51179, 32],
    [datetime.datetime(1997, 7, 1, tzinfo=pytz.utc), 50630, 31],
    [datetime.datetime(1996, 1, 1, tzinfo=pytz.utc), 50083, 30],
    [datetime.datetime(1994, 7, 1, tzinfo=pytz.utc), 49534, 29],
    [datetime.datetime(1993, 7, 1, tzinfo=pytz.utc), 49169, 28],
    [datetime.datetime(1992, 7, 1, tzinfo=pytz.utc), 48804, 27],
    [datetime.datetime(1991, 1, 1, tzinfo=pytz.utc), 48257, 26],
    [datetime.datetime(1990, 1, 1, tzinfo=pytz.utc), 47892, 25],
    [datetime.datetime(1988, 1, 1, tzinfo=pytz.utc), 47161, 24],
    [datetime.datetime(1985, 7, 1, tzinfo=pytz.utc), 46247, 23],
    [datetime.datetime(1993, 7, 1, tzinfo=pytz.utc), 45516, 22],
    [datetime.datetime(1982, 7, 1, tzinfo=pytz.utc), 45151, 21],
    [datetime.datetime(1981, 7, 1, tzinfo=pytz.utc), 44786, 20],
    [datetime.datetime(1980, 1, 1, tzinfo=pytz.utc), 44239, 19],
    [datetime.datetime(1979, 1, 1, tzinfo=pytz.utc), 43874, 18],
    [datetime.datetime(1978, 1, 1, tzinfo=pytz.utc), 43509, 17],
    [datetime.datetime(1977, 1, 1, tzinfo=pytz.utc), 43144, 16],
    [datetime.datetime(1976, 1, 1, tzinfo=pytz.utc), 42778, 15],
    [datetime.datetime(1975, 1, 1, tzinfo=pytz.utc), 42413, 14],
    [datetime.datetime(1974, 1, 1, tzinfo=pytz.utc), 42048, 13],
    [datetime.datetime(1973, 1, 1, tzinfo=pytz.utc), 41683, 12],
    [datetime.datetime(1972, 7, 1, tzinfo=pytz.utc), 41499, 11],
    [datetime.datetime(1972, 1, 1, tzinfo=pytz.utc), 41317, 10],
]
"# Leap seconds definition, [UTC datetime, MJD, DUTC]"

def bat2utc(bat, dutc=None):
    """
    Convert Binary Atomic Time (BAT) to UTC.  At the ATNF, BAT corresponds to
    the number of microseconds of atomic clock since MJD (1858-11-17 00:00).

    :param bat: number of microseconds of atomic clock time since
        MJD 1858-11-17 00:00.
    :type bat: long
    :returns utcDJD: UTC date and time (Dublin Julian Day as used by pyephem)
    :rtype: float

    """
    dutc = dutc or getDUTCDt()
    if type(bat) is str:
        bat = long(bat, base=16)
    utcMJDs = (bat/1000000.0)-dutc
    utcDJDs = utcMJDs-86400.0*15019.5
    utcDJD = utcDJDs/86400.0
    return utcDJD + 2415020 - 2400000.5

def utc_now():
    """
    Return current UTC as a timezone aware datetime.
    :rtype: datetime
    """
    dt=datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return dt

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
parser.add_argument('-g', '--nbeam', type=int, nargs='+',
                    help='Number of beams.')

def receive_metadata(length, nbeam):
    # Bind to multicast
    multicast_group = '224.1.1.1'
    server_address = ('', 5007)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create the socket
    sock.bind(server_address) # Bind to the server address
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)  # Tell the operating system to add the socket to the multicast group on all interfaces.
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, mreq)

    # Define file names and open files to write
    start_time = utc_now()
    time_str = "%Y-%m-%d-%H:%M:%S"
    metadata_fname = '{:s}/{:s}.metadata'.format(directory, start_time.strftime(time_str))
    interval_fname = '{:s}/{:s}.interval'.format(directory, start_time.strftime(time_str))
    direction_fname = '{:s}/{:s}.direction'.format(directory, start_time.strftime(time_str))
    metadata_file = open(metadata_fname, "w")
    interval_file = open(interval_fname, "w")
    direction_file = open(direction_fname, "w")
    on_source0 = 'false'  # assume to start with off-source
    
    # Start tick
    start_time = time.time()
    #old_time = 0
    while ((time.time() - start_time) < length):
        print "Metadata capture, {:f} seconds of {:f} seconds ...".format(time.time() - start_time, length)
        pkt, address = sock.recvfrom(1<<16)
        data = json.loads(pkt)
        metadata_file.write(str(data))  # To record metadata with original format
        #print (bat2utc(str(data['timestamp'])) -old_time) * 86400.0
        #old_time = bat2utc(str(data['timestamp']))
        
        on_source1 = data['pk01']['on_source']
        print on_source1
        if on_source1 != on_source0:
            interval_file.write(str(bat2utc(str(data['timestamp']))))  # To record on-source time interval
            interval_file.write("\t")
            on_source0 = on_source1
                            
            if on_source1 == "false":  # To end current on-source interval
                interval_file.write("\n")

            if on_source1 == 'true':   # To record the direction of "nbeam" beams when the telescope is on source
                direction_file.write(str(bat2utc(str(data['timestamp']))))  
                direction_file.write("\t")
                for item in range(nbeam):
                    direction_file.write(str(data['beams_direction']['beam{:02d}'.format(item+1)][0]))
                    direction_file.write('\t')
                    direction_file.write(str(data['beams_direction']['beam{:02d}'.format(item+1)][1]))
                    direction_file.write('\t')
                direction_file.write('\n')
        metadata_file.write("\n")

    sock.close()
    metadata_file.close()
    interval_file.close()
    direction_file.close()

#length = 10
#nbeam  = 9
#receive_metadata(length, nbeam)
#exit()

args         = parser.parse_args()
cfname       = args.cfname[0]
numa         = args.numa[0]
nic          = numa + 1
visiblegpu   = args.visiblegpu[0]
directory    = args.directory[0]
memcheck     = args.memcheck[0]
length       = args.length[0]
nbeam        = args.nbeam[0]

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

def metadata(length, nbeam):
    receive_metadata(length, nbeam)
    
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

    t_metadata = threading.Thread(target = receive_metadata, args=(length, nbeam,))
    t_capture  = threading.Thread(target = capture)
    t_baseband2power = threading.Thread(target = baseband2power)
    t_dbdisk    = threading.Thread(target = dbdisk)

    t_metadata.start()
    t_capture.start()
    t_baseband2power.start()
    t_dbdisk.start()

    t_metadata.join()
    t_capture.join()
    t_baseband2power.join()
    t_dbdisk.join()

    os.system("dada_db -d -k {:s}".format(capture_key))
    os.system("dada_db -d -k {:s}".format(baseband2power_key))
    
if __name__ == "__main__":
    main()
