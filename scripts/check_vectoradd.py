#!/usr/bin/env python3
#
# Yineng Yan (yinengy@umich.edu, 2020

import sys

base_addr = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

map_thread_addr = {}

# read input and build dict
for line in sys.stdin:
    if "#ld#" in line: # format: "#ld#is_shared_memory, blockid, threadid, addr\n"
        temp = line[4:-1].split(",")
        tid = int(temp[-2])
        addr = int(temp[-1], 0)       


    if "#st#" in line: # format: "#ld#is_shared_memory, blockid, threadid, addr\n"
        temp = line[4:-1].split(",")
        tid = int(temp[-2])
        addr = int(temp[-1], 0)  

        map_thread_addr[tid] = addr

        if (tid == 1):
            base_addr = addr - 8

for tid in map_thread_addr:
    c_idx = (map_thread_addr[tid] - base_addr) // 8

    if (c_idx != tid):
        print("Base addr is " + str(base_addr))
        print("Thread " + str(tid) + " write to c[" + str(c_idx) + "]" + "and address is " + str(map_thread_addr[tid]))
        print("Thread " + str(0) + " write to  address is " + str(map_thread_addr[0]))
        print("Thread " + str(1) + " write to  address is " + str(map_thread_addr[1]))
        raise Exception("Error")
    print("Thread " + str(tid) + " write to c[" + str(c_idx) + "]")