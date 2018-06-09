#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

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
    time_sample  = mjd_start + tsamp * np.arange(nsamp)/86400.0
    
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
    return direction_sample, power_sample

if __name__ == "__main__":
    beam       = 0
    time_stamp = "2018-06-09-07:37:10"
    ddir       = "/beegfs/DENG/JUNE/beam{:d}".format(beam)
    freq       = 100
    
    direction_sample, power_sample = main(beam, time_stamp, ddir)
    # Plot the result here, use imshow
    
