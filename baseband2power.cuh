#ifndef _BASEBAND2POWER_CUH
#define _BASEBAND2POWER_CUH

#include <cuda_runtime.h>
#include <cuda.h>
#include <cufft.h>
#include <stdio.h>

#include "dada_cuda.h"
#include "dada_hdu.h"
#include "dada_def.h"
#include "ipcio.h"
#include "ascii_header.h"
#include "daemon.h"
#include "futils.h"
#include "paf_baseband2power.cuh"

typedef struct conf_t
{
  int device_id;
  char dir[MSTR_LEN];
  key_t key_in, key_out;
}conf_t;

#endif