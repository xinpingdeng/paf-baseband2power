#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <time.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <inttypes.h>
#include <math.h>

#include "multilog.h"
#include "baseband2power.cuh"
#include "paf_baseband2power.cuh"
#include "cudautil.cuh"
#include "kernel.cuh"
