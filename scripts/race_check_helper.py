#!/usr/bin/env python3
#
# The script will read stdin 
# (which should be output of NVbit tool "print_data_race").
# And it will grep load and store. 
# Will check if there are conflicting memory accesses (data races)
# A warning will be printed
#
#
# Yineng Yan (yinengy@umich.edu, 2020

import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Address:
    def __init__(self):
        self.load = set() # set of thread id that read from this address
        self.store = set() # set of thread id that write to this address


shared_mem = {} 
global_mem = {}

# read input and build dict
for line in sys.stdin:
    if "#ld#" in line: # format: "#ld#is_shared_memory, blockid, threadid, addr\n"
        temp = line[4:-1].split(",")
        addr = temp[-1]

        if (temp[0] == '1'): # shared memory
            continue # TODO: support shared memory
        else: # global memory
            if addr not in global_mem:
                a = Address()
                a.load.add(temp[-2]) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].load.add(temp[-2])          


    elif "#st#" in line: # format: "#st#is_shared_memory, blockid, threadid, addr\n"
        temp = line[4:-1].split(",")
        addr = temp[-1]

        if (temp[0] == '1'): # shared memory
            continue # TODO: support shared memory
        else:
            if addr not in global_mem:
                a = Address()
                a.store.add(temp[-2]) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].store.add(temp[-2])

flag = False

# print warning
for addr, addr_obj in global_mem.items():
    if (len(addr_obj.load) > 1 and len(addr_obj.store) > 1) or \
        (len(addr_obj.load) == 1 and len(addr_obj.store) == 1 and addr_obj.load != addr_obj.store):
        print(bcolors.WARNING + "Warning! There may be a data race in address(Global): " + addr + " where:" + bcolors.ENDC)
       
        print("\tLoad from threads: ", end="")
        for l in addr_obj.load:
            print(l, end=" ")

        print("")

        print("\tStore from threads: ", end="")
        for s in addr_obj.store:
            print(s, end=" ")

        print("\n")
        flag = True

if not flag:
    print(bcolors.OKGREEN + "no data races found."+ bcolors.ENDC)