#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import ephem
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import axes3d
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import interp2d
from scipy.interpolate import BivariateSpline
from scipy.interpolate import griddata

def keyword_value(data_file, nline_header, key_word):
    data_file.seek(0)  # Go to the beginning of DADA file
    for iline in range(nline_header):
        line = data_file.readline()
        if key_word in line and line[0] != '#':
            mjd_start = float(line.split()[1])
            return mjd_start
    print "Can not find the keyword \"{:s}\" in header ...".format(key_word)
    exit(1)

def power_cal(beam, time_stamp, ddir):
    # Some special case for file name
    if time_stamp == "2018-06-26-18:31:15":
        time_stamp = "2018-06-26-18:31:16"
    if time_stamp == "2018-06-26-20:59:41":
        time_stamp = "2018-06-26-20:59:42"
    if time_stamp == "2018-06-27-15:30:43":
        time_stamp = "2018-06-27-15:30:44"
    if time_stamp == "2018-06-27-16:21:04":
        time_stamp = "2018-06-27-16:21:05"

    power_fname     = "{:s}/{:s}_0000000000000000.000000.dada".format(ddir, time_stamp)
    
    hdr_size     = 4096
    power_file   = open(power_fname, "r")
    
    # To get the essential values from DADA header
    nline_header = 50  # Slightly larger than real lines
    key_word     = "MJD_START"
    mjd_start    = float(keyword_value(power_file, nline_header, key_word))
    key_word     = "TSAMP"
    tsamp        = float(keyword_value(power_file, nline_header, key_word))/1E6 # Convert to second
    key_word     = "FILE_SIZE"
    file_size    = int(keyword_value(power_file, nline_header, key_word))
    key_word     = "NCHAN"
    nchan        = int(keyword_value(power_file, nline_header, key_word))
    key_word     = "NBIT"
    nbit         = int(keyword_value(power_file, nline_header, key_word))
    nsamp        = 8 * file_size / (nchan * nbit)
    
    # Read data sample from DADA file
    power_file.seek(hdr_size)
    power = np.array(np.fromstring(power_file.read(nsamp * nchan * nbit / 8), dtype='float32'))
    power = np.reshape(power, (nsamp, nchan))
    time  = mjd_start + tsamp * np.arange(nsamp)/86400.0 + 3.5 / 86400.0
    
    power_file.close()
    return time, power

def direction_cal(beam, time_stamp, ddir, time):
    direction_fname = "{:s}/{:s}.direction".format(ddir, time_stamp)
    direction_data = np.loadtxt(direction_fname)
    direction_interp = []
    direction_interp.append(np.interp(time, direction_data[:,0], direction_data[:, 2 * beam + 1]))
    direction_interp.append(np.interp(time, direction_data[:,0], direction_data[:, 2 * beam + 2]))
    direction_interp = np.array(direction_interp).T

    return direction_interp

def main(beam, time_stamp, ddir):
    time, power = power_cal(beam, time_stamp, ddir)
    direction = direction_cal(beam, time_stamp, ddir, time)

    # 3C286
    beam = ephem.FixedBody()
    src = ephem.FixedBody()
    src._ra, src._dec = "13:31:08.28556", "+30:30:32.4990"
    # 3C147
    #src._ra, src._dec = "05:42:36.2646", "+49:51:07.083"
    
    # Effelsberg
    eff = ephem.Observer()
    eff.long, eff.lat = '6.883611111', '50.52483333'

    radec_delta = []
    azele_delta = []
    len_direction = len(direction)
    for i in range(len_direction):
        delta_tmp = []
        eff.date = time[i] - 15019.5
        beam._ra, beam._dec = direction[i,0], direction[i,1]
        
        beam.compute(eff)
        src.compute(eff)

        azele_delta.append([beam.az - src.az, beam.alt - src.alt])
        radec_delta.append([beam.ra - src.ra, beam.dec - src.dec])
    azele_delta = np.array(azele_delta)
    radec_delta = np.array(radec_delta)
    
    return time, radec_delta * 180/np.pi * 60, azele_delta * 180/np.pi * 60, power

if __name__ == "__main__":
    beam       = 0
    time_stamp = "2018-06-29-17:44:40"
    #time_stamp = "2018-06-29-18:13:02"
    #time_stamp = '2018-06-26-20:01:17'
    #time_stamp = "2018-06-29-15:49:37"
    #time_stamp = "2018-06-30-13:05:31"
    time_stamp = "2018-06-30-13:32:19"

    #beam       = 0
    #time_stamp = "2018-06-26-19:30:02"
    #beam       = 1
    #time_stamp = "2018-06-26-19:30:02"
    #beam       = 2
    #time_stamp = "2018-06-26-19:29:59"
    #beam       = 3
    #time_stamp = "2018-06-26-19:29:58"
    #beam       = 4
    #time_stamp = "2018-06-26-19:29:53"
    #beam       = 5
    #time_stamp = "2018-06-26-19:29:53"
    #beam       = 6
    #time_stamp = "2018-06-26-19:29:35"
    #beam       = 7
    #time_stamp = "2018-06-26-19:29:35"
    #beam       = 8
    #time_stamp = "2018-06-26-19:29:29"

    begin      = 10
    end        = -10
    ddir       = "/beegfs/DENG/docker/beam{:d}".format(beam)
    time, radec_delta, azele_delta, power = main(beam, time_stamp, ddir)

    plt.figure()
    plt.subplot(2,1,1)
    plt.plot(radec_delta[begin:end,0], radec_delta[begin:end,1])
    plt.subplot(2,1,2)
    plt.plot(azele_delta[begin:end,0], azele_delta[begin:end,1])
    plt.show()

    freq = 210
    x = radec_delta[begin:end,0]
    y = radec_delta[begin:end,1]
    #x = azele_delta[begin:end,0]
    #y = azele_delta[begin:end,1]
    z = power[begin:end, freq]

    plt.figure()
    plt.subplot(2,1,1)
    plt.plot(x, z)
    plt.subplot(2,1,2)
    plt.plot(y, z)
    plt.show()
    
    xinterval = max(x)-min(x)
    maxx = max(x) - xinterval * 0.1
    minx = min(x) + xinterval * 0.1
    yinterval = max(y) - min(y)
    maxy = max(y) - yinterval * 0.1
    miny = min(y) + yinterval * 0.1

    #minx, maxx = -8.5, 8.5
    #miny, maxy = -8.5, 8.5
    
    xi = np.linspace(minx, maxx,len(x))
    yi = np.linspace(miny, maxy,len(y))

    print minx -maxx, miny - maxy
    print xinterval, yinterval

    print maxx, minx, maxy, miny
    X,Y= np.meshgrid(xi,yi)

    zi = griddata((x, y), z, (X,Y), method='linear')

    plt.figure()
    #plt.imshow(zi, interpolation = 'hanning', aspect="auto", extent = [minx, maxx, miny, maxy])
    plt.imshow(zi, interpolation = 'hanning', aspect="auto")#, extent = [-10, 10, -10, 10])
    plt.xlabel("Azimuth offset (arcmin)")
    plt.ylabel("Elevation offset (arcmin)")
    plt.show()
