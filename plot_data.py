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
#RectBivariateSpline

def keyword_value(data_file, nline_header, key_word):
    data_file.seek(0)  # Go to the beginning of DADA file
    for iline in range(nline_header):
        line = data_file.readline()
        if key_word in line and line[0] != '#':
            mjd_start = float(line.split()[1])
            return mjd_start
    print "Can not find the keyword \"{:s}\" in header ...".format(key_word)
    exit(1)

def power(beam, time_stamp, ddir):
    #time_stamp = "2018-06-26-18:31:16"
    #time_stamp = "2018-06-26-20:59:42"
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
    power_sample = np.array(np.fromstring(power_file.read(nsamp * nchan * nbit / 8), dtype='float32'))
    power_sample = np.reshape(power_sample, (nsamp, nchan))
    #time_sample  = mjd_start + tsamp * np.arange(nsamp)/86400.0 + 2*tsamp/86400.0
    time_sample  = mjd_start + tsamp * np.arange(nsamp)/86400.0 + 3.5 / 86400.0
    
    power_file.close()
    return time_sample, power_sample

def direction(beam, time_stamp, ddir, time_sample):
    direction_fname = "{:s}/{:s}.direction".format(ddir, time_stamp)
    direction_data = np.loadtxt(direction_fname)
    direction_interp = []
    direction_interp.append(np.interp(time_sample, direction_data[:,0], direction_data[:, 2 * beam + 1]))
    direction_interp.append(np.interp(time_sample, direction_data[:,0], direction_data[:, 2 * beam + 2]))
    direction_interp = np.array(direction_interp).T

    return direction_interp

def main(beam, time_stamp, ddir):
    time_sample, power_sample = power(beam, time_stamp, ddir)
    direction_sample = direction(beam, time_stamp, ddir, time_sample)

    # 3C286
    beam = ephem.FixedBody()
    src = ephem.FixedBody()
    #src._ra, src._dec = "13:31:08.3", "+30:30:33"
    #src._ra, src._dec = "13:28:49.66", "+30:45:58.3"
    src._ra, src._dec = "13:31:08.28556", "+30:30:32.4990"
    
    # Effelsberg
    eff = ephem.Observer()
    eff.long, eff.lat = '6.883611111', '50.52483333'

    direction_delta = []
    len_direction = len(direction_sample)
    for i in range(len_direction):
        beam_direction = []
        eff.date = time_sample[i] - 15019.5
        beam._ra, beam._dec = direction_sample[i,0], direction_sample[i,1]
        #beam._ra, beam._dec = "13:31:08.3", "+30:30:33"
        
        beam.compute(eff)
        src.compute(eff)

        #beam_direction.append(beam.az - src.az)
        #beam_direction.append(beam.az)
        #beam_direction.append(beam.alt * np.cos(beam.az))
        #beam_direction.append(beam.alt)
        #beam_direction.append(beam.az * np.cos(beam.alt))
        #beam_direction.append((beam.az - src.az) * np.cos(src.alt))

        beam_direction.append(beam.ra - src.ra)
        #beam_direction.append(beam.az*np.cos(beam.alt))
        beam_direction.append((beam.dec - src.dec))
        direction_delta.append(beam_direction)
    direction_delta = np.array(direction_delta)
    
    return time_sample, direction_sample, direction_delta, power_sample

if __name__ == "__main__":
    beam       = 0
    #time_stamp = "2018-06-09-07:37:10"
    #time_stamp = "2018-06-25-20:12:41"
    #time_stamp = "2018-06-26-17:52:22"
    #time_stamp = "2018-06-26-17:59:52"
    #time_stamp = "2018-06-26-18:31:15"
    #time_stamp = "2018-06-26-18:44:48"
    #time_stamp = "2018-06-26-19:08:34"
    #time_stamp = "2018-06-26-20:59:41"
    #time_stamp = "2018-06-26-21:24:46"
    
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
    beam       = 8
    time_stamp = "2018-06-26-19:29:29"

    #beam       = 0
    #time_stamp = "2018-06-26-20:01:17"
    #beam       = 1
    #time_stamp = "2018-06-26-20:01:12"
    #beam       = 2
    #time_stamp = "2018-06-26-20:01:03"
    #beam       = 3
    #time_stamp = "2018-06-26-20:01:05"
    #beam       = 4
    #time_stamp = "2018-06-26-20:01:06"
    #beam       = 5
    #time_stamp = "2018-06-26-20:01:06"
    #beam       = 6
    #time_stamp = "2018-06-26-20:01:02"
    #beam       = 7
    #time_stamp = "2018-06-26-20:00:59"
    #beam       = 8
    #time_stamp = "2018-06-26-20:00:57"
    
    #ddir       = "/beegfs/DENG/JUNE/beam{:d}".format(beam)
    ddir       = "/beegfs/DENG/docker/beam{:d}".format(beam)
    freq       = 100
    
    time_sample, direction_sample, direction_delta, power_sample = main(beam, time_stamp, ddir)
    
    #freq = 260
    #plt.figure()
    #plt.subplot(2,1,1)
    #plt.plot(direction_sample[:,0] * 180.0/np.pi, power_sample[:,freq])
    ##plt.plot(time_sample, power_sample[:,freq])
    ##plt.xlim([202, 203.5])
    #plt.subplot(2,1,2)
    #plt.plot(direction_sample[:,1] * 180.0/np.pi, power_sample[:,freq])
    #plt.xlim([29, 31])
    #plt.show()

    #freq = 200    
    #f        = interp2d(direction_sample[:,0], direction_sample[:,1], power_sample[:, freq], kind="cubic")
    #x_coords = np.arange(min(direction_sample[:,0]),max(direction_sample[:,0]), (max(direction_sample[:,0]) - min(direction_sample[:,0]))/len(direction_sample[:,0]))
    #y_coords = np.arange(min(direction_sample[:,1]),max(direction_sample[:,1]), (max(direction_sample[:,1]) - min(direction_sample[:,1]))/len(direction_sample[:,1]))
    #z        = f(x_coords,y_coords)
    #
    #fig = plt.imshow(z,
    #                 extent=[min(direction_sample[:,0]),max(direction_sample[:,0]),min(direction_sample[:,1]),max(direction_sample[:,1])],
    #                 origin="lower")
    #plt.show()
    #
    #plt.figure()
    #plt.plot(x_coords, z)
    #plt.show()

    #freq = 200
    #fig = plt.figure()
    #ax = plt.axes(projection='3d')
    #surf = ax.plot_surface(direction_sample[:,0] * 180/np.pi, direction_sample[:,1] * 180/np.pi, power_sample[:,freq], cmap=plt.cm.jet, rstride=1, cstride=1, linewidth=0)
    ## Add a color bar which maps values to colors.
    #fig.colorbar(surf, shrink=0.5, aspect=5)
    #plt.show()

    #data = np.reshape(power_sample[:,freq][5:256+5], (16,16))
    #
    #plt.figure()
    #plt.imshow(data)
    #plt.show()

    #freq = 200
    #f = BivariateSpline(direction_sample[:,0], direction_sample[:,1], power_sample[:, freq], kind='cubic')
    #data = f(direction_sample[:,0], direction_sample[:,1])
    #
    #plt.figure()
    #plt.plot(direction_sample[:,1], data)
    #plt.show()

    #plt.figure()
    #plt.subplot(2,1,1)
    #plt.plot(time_sample, direction_sample[:,0])
    #plt.subplot(2,1,2)
    #plt.plot(time_sample, direction_sample[:,1])
    #plt.show()
    
    #freq = 200
    #x = direction_sample[:,0] * 180/np.pi
    #y = direction_sample[:,1] * 180/np.pi
    #z = power_sample[:,freq]
    #
    ##plt.figure()
    ##plt.plot((time_sample - time_sample[0]) * 86400.0, x)
    ##plt.show()
    #
    ##plt.figure()
    ##plt.subplot(2,1,1)
    ##plt.plot(x, z)
    ##plt.subplot(2,1,2)
    ##plt.plot(y, z)
    ##plt.show()
    #
    ##x, y = np.meshgrid(x, y)
    ##
    ##z = np.meshgrid(z)
    #
    #
    ##plt.figure()
    ##plt.imshow(z)
    ##plt.show()
    #
    ##print x
    ##print y
    ##print z
    #
    ##plt.figure()
    ##X,Y = np.meshgrid(x,y)
    ##Z = z.reshape(len(y),len(x))
    ##plt.pcolormesh(X,Y,Z)
    ##
    ##plt.show()
    #
    ##b = np.concatenate(([x], [y], [z]), axis=0).T
    ##
    ##plt.figure()
    ##plt.pcolor(b)
    ##plt.show()
    #
    #plt.figure()
    #plt.plot(x, z)
    #plt.show()

    
