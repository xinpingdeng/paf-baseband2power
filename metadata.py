#!/usr/bin/env python

import socket 
import json
import datetime 
import pytz

def utc_now():
    """
    Return current UTC as a timezone aware datetime.
    :rtype: datetime
    """
    dt=datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return dt

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

NBEAM = 36

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind(("134.104.74.36", 26666))

    fp = open('{:s}.txt'.format(utc_now().strftime("%Y%m%d%H%M")), 'w')
    #start_time = utc_now()
    
    while True:
        pkt, addr = sock.recvfrom(1<<16) 
        data = json.loads(pkt)#['beams_direction']#['beam01']
        metadata = []
        metadata.append("{:.10f}\t".format(bat2utc(str(data['timestamp']))))
        for item in range(NBEAM):
            beam_position = data['beams_direction']['beam{:02d}'.format(item+1)]
            metadata.append("{:s}\t{:s}\t".format(beam_position[0], beam_position[1]))
        metadata.append('\n')
        
        fp.writelines(metadata)
        #if((utc_now() - start_time) > datetime.timedelta(minutes = 1)):
        #    fp.close()
        #
        #    start_time = utc_now()
        #    fp = open('{:s}.txt'.format(utc_now().strftime("%Y%m%d%H%M")), 'w')
    fp.close()
