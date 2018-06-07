#!/usr/bin/env python

import os
import numpy as np
import matplotlib.pyplot as plt

fdir    = "/beegfs/DENG/docker"
fname   = "2018-04-17-19:22:11_0000000000000000.000000.dada"
#fname   = "2018-06-07-13:30:48_0000000000026880.000000.dada"
nchan   = 336
dsize   = 4
hdrsize = 4096

fname = os.path.join(fdir, fname)
f = open(fname, "r")

f.seek(hdrsize)
sample = np.array(np.fromstring(f.read(nchan * dsize), dtype='float32'))
f.close()
print sample

plt.figure()
plt.plot(sample)
plt.show()
