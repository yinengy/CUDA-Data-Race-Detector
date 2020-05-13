/* 
 *
 * A NVBit tool, which will detect conflict memory access in the kernel.
 * The raw output will be processed by a Pytyhon script
 *
 * Yineng Yan (yinengy@umich.edu), 2020
 */

#include <stdint.h>
#include <stdio.h>

#include "utils/utils.h"

extern "C" __device__ __noinline__ void print_ldst(
        int pred,
        uint64_t addr,
        int32_t is_shared_memory,
        int32_t is_load) {
    /* if predicate is off return */
    if (!pred) {
        return;
    }

    /* compute thread id and warp id */
    int threadid = blockIdx.x * blockDim.x + threadIdx.x;
    int blockid = blockIdx.x * blockDim.x * blockDim.y * blockDim.z + 
            threadIdx.z * blockDim.y * blockDim.x + 
            threadIdx.y * blockDim.x + threadIdx.x;

    /* "#{ld/st}#" is used to grep */
    if (is_load) {
        printf("#ld#%d,%d,%d,0x%016lx\n",
            is_shared_memory, blockid, threadid, addr);
    } else {
        printf("#st#%d,%d,%d,0x%016lx\n",
            is_shared_memory, blockid, threadid, addr);
    }

}