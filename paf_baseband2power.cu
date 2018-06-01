#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>

#include "multilog.h"
#include "baseband2power.cuh"
#include "paf_baseband2power.cuh"
#include "cudautil.cuh"
#include "kernel.cuh"

void usage ()
{
  fprintf (stdout,
	   "paf_baseband2power - To detect baseband data with original channels and average the detected data in time\n"
	   "\n"
	   "Usage: paf_process [options]\n"
	   " -a  Hexacdecimal shared memory key for incoming ring buffer\n"
	   " -b  Hexacdecimal shared memory key for outcoming ring buffer\n"
	   " -c  The name of the directory in which we will record the data\n"
	   " -d  The index of GPU\n"
	   " -h  show help\n");
}

multilog_t *runtime_log;

int main(int argc, char *argv[])
{
  int arg;
  FILE *fp_log = NULL;
  char log_fname[MSTR_LEN];
  conf_t conf;
  
  /* configuration from command line */
  while((arg=getopt(argc,argv,"a:b:c:d:h:")) != -1)
    {
      switch(arg)
	{
	case 'h':
	  usage();
	  return EXIT_FAILURE;
	  
	case 'a':	  	  
	  if (sscanf (optarg, "%x", &conf.key_in) != 1)
	    {
	      fprintf (stderr, "Could not parse key from %s, which happens at \"%s\", line [%d].\n", optarg, __FILE__, __LINE__);
	      return EXIT_FAILURE;
	    }
	  break;
	  	
	case 'b':	  	  
	  if (sscanf (optarg, "%x", &conf.key_out) != 1)
	    {
	      fprintf (stderr, "Could not parse key from %s, which happens at \"%s\", line [%d].\n", optarg, __FILE__, __LINE__);
	      return EXIT_FAILURE;
	    }
	  break;
	  		  
	case 'c':
	  sscanf(optarg, "%s", conf.dir);
	  break;

	case 'd':
	  sscanf(optarg, "%d", &conf.device_id);
	  break;	  
	}
    }
  
  /* Setup log interface */
  sprintf(log_fname, "%s/paf_baseband2power.log", conf.dir);
  fp_log = fopen(log_fname, "ab+");
  if(fp_log == NULL)
    {
      fprintf(stderr, "Can not open log file %s\n", log_fname);
      return EXIT_FAILURE;
    }
  runtime_log = multilog_open("paf_baseband2power", 1);
  multilog_add(runtime_log, fp_log);
  multilog(runtime_log, LOG_INFO, "START PAF_PROCESS\n");
  
  /* Here to make sure that if we only expose one GPU into docker container, we can get the right index of it */ 
  int deviceCount;
  CudaSafeCall(cudaGetDeviceCount(&deviceCount));
  if(deviceCount == 1)
    conf.device_id = 0;

  return EXIT_SUCCESS;
}
