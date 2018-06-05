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

extern multilog_t *runtime_log;

int init_baseband2power(conf_t *conf)
{
  CudaSafeCall(cudaSetDevice(conf->device_id));
  size_t curbufsz;
  uint64_t block_id;
  
  ipcbuf_t *db = NULL;
  if(conf->nchan_out != (NCHAN_CHK * NCHK_NIC))
    {
      multilog(runtime_log, LOG_ERR, "Channel number mismatch\n");
      fprintf(stderr, "The number of channel is not match %d != %d, which happens at \"%s\", line [%d].\n",conf->nchan_out, NCHAN_CHK * NCHK_NIC, __FILE__, __LINE__);
    }
  conf->bufin_size  = conf->rbufin_ndf * NCHAN_CHK * NCHK_NIC * NSAMP_DF * NPOL_SAMP * NDIM_POL * NBYTE_IN;
  conf->bufrt_size  = conf->rbufin_ndf * NCHAN_CHK * NCHK_NIC * NSAMP_DF * NPOL_SAMP * NDIM_POL * NBYTE_RT;
  conf->bufout_size = NCHAN_CHK * NCHK_NIC * NBYTE_OUT;
  
  conf->nsamp_in  = conf->rbufin_ndf * NCHAN_CHK * NCHK_NIC * NSAMP_DF;
  conf->nsamp_rt  = conf->nsamp_in;
  conf->nsamp_out = conf->nchan_out;

  CudaSafeCall(cudaMalloc((void **)&conf->dbuf_in, conf->bufin_size));
  CudaSafeCall(cudaMalloc((void **)&conf->dbuf_out, conf->bufout_size));
  CudaSafeCall(cudaMalloc((void **)&conf->buf_rt, conf->bufrt_size));
  
  /* Prepare the setup of kernels */
  conf->gridsize_unpack.x = conf->rbufin_ndf;
  conf->gridsize_unpack.y = NCHK_NIC;
  conf->gridsize_unpack.z = 1;
  conf->blocksize_unpack.x = NSAMP_DF; 
  conf->blocksize_unpack.y = NCHAN_CHK;
  conf->blocksize_unpack.z = 1;

  /* Attach to input ring buffer */
  conf->hdu_in = dada_hdu_create(runtime_log);
  dada_hdu_set_key(conf->hdu_in, conf->key_in);
  if(dada_hdu_connect(conf->hdu_in) < 0)
    {
      multilog(runtime_log, LOG_ERR, "could not connect to hdu\n");
      fprintf(stderr, "Can not connect to hdu, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }  
  db = (ipcbuf_t *) conf->hdu_in->data_block;
  if(ipcbuf_get_bufsz(db) != conf->bufin_size)
    {
      multilog(runtime_log, LOG_ERR, "data buffer size mismatch\n");
      fprintf(stderr, "Buffer size mismatch, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }

  /* registers the existing host memory range for use by CUDA */
  dada_cuda_dbregister(conf->hdu_in);
  
  if(ipcbuf_get_bufsz(conf->hdu_in->header_block) != DADA_HDR_SIZE)    // This number should match
    {
      multilog(runtime_log, LOG_ERR, "Header buffer size mismatch\n");
      fprintf(stderr, "Buffer size mismatch, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }
  
  /* make ourselves the read client */
  if(dada_hdu_lock_read(conf->hdu_in) < 0)
    {
      multilog(runtime_log, LOG_ERR, "open_hdu: could not lock write\n");
      fprintf(stderr, "Error locking HDU, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  
  /* Prepare output ring buffer */
  conf->hdu_out = dada_hdu_create(runtime_log);
  dada_hdu_set_key(conf->hdu_out, conf->key_out);
  if(dada_hdu_connect(conf->hdu_out) < 0)
    {
      multilog(runtime_log, LOG_ERR, "could not connect to hdu\n");
      fprintf(stderr, "Can not connect to hdu, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }
  db = (ipcbuf_t *) conf->hdu_out->data_block;
  if(ipcbuf_get_bufsz(db) != conf->bufout_size)  
    {
      multilog(runtime_log, LOG_ERR, "data buffer size mismatch\n");
      fprintf(stderr, "Buffer size mismatch, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }
  
  if(ipcbuf_get_bufsz(conf->hdu_out->header_block) != DADA_HDR_SIZE)    // This number should match
    {
      multilog(runtime_log, LOG_ERR, "Header buffer size mismatch\n");
      fprintf(stderr, "Buffer size mismatch, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;    
    }  
  /* make ourselves the write client */
  if(dada_hdu_lock_write(conf->hdu_out) < 0)
    {
      multilog(runtime_log, LOG_ERR, "open_hdu: could not lock write\n");
      fprintf(stderr, "Error locking HDU, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  
  if(conf->sod)
    {      
      if(ipcbuf_enable_sod(db, 0, 0) < 0)  // We start at the beginning
  	{
	  multilog(runtime_log, LOG_ERR, "Can not write data before start, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
  	  fprintf(stderr, "Can not write data before start, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
  	  return EXIT_FAILURE;
  	}
    }
  else
    {
      if(ipcbuf_disable_sod(db) < 0)
  	{
	  multilog(runtime_log, LOG_ERR, "Can not write data before start, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
  	  fprintf(stderr, "Can not write data before start, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
  	  return EXIT_FAILURE;
  	}
    }
  
  /* Register header */
  if(register_header(conf))
    {
      multilog(runtime_log, LOG_ERR, "header register failed, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      fprintf(stderr, "header register failed, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }

  conf->hdu_out->data_block->curbuf = ipcio_open_block_write(conf->hdu_out->data_block, &block_id);   /* Open buffer to write */
  conf->hdu_in->data_block->curbuf = ipcio_open_block_read(conf->hdu_in->data_block, &curbufsz, &block_id);
    
  return EXIT_SUCCESS;
}

int destroy_process(conf_t conf)
{
  CudaSafeCall(cudaSetDevice(conf.device_id));

  cudaFree(conf.dbuf_in);
  cudaFree(conf.dbuf_out);
  cudaFree(conf.buf_rt);

  dada_cuda_dbunregister(conf.hdu_in);
  dada_hdu_unlock_read(conf.hdu_in);
  dada_hdu_unlock_write(conf.hdu_out);
  
  return EXIT_SUCCESS;
}

int do_baseband2power(conf_t conf)
{
  CudaSafeCall(cudaSetDevice(conf.device_id));
  size_t curbufsz;
  uint64_t block_id;
  
#ifdef DEBUG
  struct timespec start, stop;
  double elapsed_time;
#endif
  
  while(conf.hdu_in->data_block->curbufsz == conf.bufin_size)
    {
#ifdef DEBUG
      clock_gettime(CLOCK_REALTIME, &start);
#endif

      CudaSafeCall(cudaMemcpy(conf.dbuf_in, conf.hdu_in->data_block->curbuf, conf.bufin_size, cudaMemcpyHostToDevice));
      
#ifdef DEBUG
      clock_gettime(CLOCK_REALTIME, &stop);
      elapsed_time = (stop.tv_sec - start.tv_sec) + (stop.tv_nsec - start.tv_nsec)/1000000000.0L;
      fprintf(stdout, "Elapsed time to copy %"PRIu64" bytes data is %f second.\n", conf.bufin_size, elapsed_time);
#endif
      
      if(ipcio_close_block_read(conf.hdu_in->data_block, conf.hdu_in->data_block->curbufsz)<0)
      	{
	  multilog (runtime_log, LOG_ERR, "close_buffer: ipcio_close_block_write failed\n");
	  fprintf(stderr, "close_buffer: ipcio_close_block_write failed, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
	  return EXIT_FAILURE;
	}

      fprintf(stdout, "HERE\n");
      
      conf.hdu_in->data_block->curbuf = ipcio_open_block_read(conf.hdu_in->data_block, &curbufsz, &block_id);
      
      CudaSafeCall(cudaMemcpy(conf.hdu_out->data_block->curbuf, conf.dbuf_out, conf.bufout_size, cudaMemcpyDeviceToHost));

      if(ipcio_close_block_write(conf.hdu_out->data_block, conf.bufout_size)<0)
	{
	  multilog (runtime_log, LOG_ERR, "close_buffer: ipcio_close_block_write failed\n");
	  fprintf(stderr, "close_buffer: ipcio_close_block_write failed, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
	  return EXIT_FAILURE;
	}

      conf.hdu_out->data_block->curbuf = ipcio_open_block_write(conf.hdu_out->data_block, &block_id);   /* Open buffer to write */     
    }
  
  return EXIT_SUCCESS;
}

int register_header(conf_t *conf)
{
  size_t hdrsz;
  
  conf->hdrbuf_in  = ipcbuf_get_next_read(conf->hdu_in->header_block, &hdrsz);
  if(hdrsz != DADA_HDR_SIZE)
    {
      multilog(runtime_log, LOG_ERR, "get next header block error.\n");
      fprintf(stderr, "Header size mismatch, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  if (!conf->hdrbuf_in)
    {
      multilog(runtime_log, LOG_ERR, "get next header block error.\n");
      fprintf(stderr, "Error getting header_buf, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  
  conf->hdrbuf_out = ipcbuf_get_next_write(conf->hdu_out->header_block);
  if (!conf->hdrbuf_out)
    {
      multilog(runtime_log, LOG_ERR, "get next header block error.\n");
      fprintf(stderr, "Error getting header_buf, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  memcpy(conf->hdrbuf_out, conf->hdrbuf_in, DADA_HDR_SIZE);
  if (ipcbuf_mark_filled (conf->hdu_out->header_block, DADA_HDR_SIZE) < 0)
    {
      multilog(runtime_log, LOG_ERR, "Could not mark filled header block\n");
      fprintf(stderr, "Error header_fill, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  
  if(ipcbuf_mark_cleared (conf->hdu_in->header_block))  // We are the only one reader, so that we can clear it after read;
    {
      multilog(runtime_log, LOG_ERR, "Could not clear header block\n");
      fprintf(stderr, "Error header_clear, which happens at \"%s\", line [%d].\n", __FILE__, __LINE__);
      return EXIT_FAILURE;
    }
  
  return EXIT_SUCCESS;
}