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

class Thread:
    def __init__(self, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id):
        self.cta_id_x = cta_id_x
        self.cta_id_y = cta_id_y
        self.cta_id_z = cta_id_z
        self.warp_id = warp_id
        self.lane_id = lane_id

    def __hash__(self):
         return hash((self.cta_id_x, self.cta_id_y, self.cta_id_z, self.warp_id, self.lane_id))
    
    def __eq__(self, other):
        return self.cta_id_x == other.cta_id_x and \
        self.cta_id_y == other.cta_id_y and \
        self.cta_id_z == other.cta_id_z and \
        self.warp_id == other.warp_id and \
        self.lane_id == other.lane_id

    def __str__(self):
        return "({} {} {} {} {})".format(self.cta_id_x, self.cta_id_y, self.cta_id_z, self.warp_id, self.lane_id)

shared_mem = {} 
global_mem = {}

# read input and build dict
for line in sys.stdin:
    temp = line[4:-1].split(",")
    if (len(temp) != 7):  # skip unwanted output
        continue

    addr = temp[-1]
    t = Thread(temp[1], temp[2], temp[3], temp[4], temp[5])

    if "#ld#" in line: # format: "#ld#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id, addr\n"
        if (temp[0] == '1'): # shared memory
            continue # TODO: support shared memory
        else: # global memory
            if addr not in global_mem:
                a = Address()
                a.load.add(t) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].load.add(t)          


    elif "#st#" in line: # format: "#st#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id, addr\n"
        if (temp[0] == '1'): # shared memory
            continue # TODO: support shared memory
        else:
            if addr not in global_mem:
                a = Address()
                a.store.add(t) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].store.add(t)       

flag = False

race_counter = 0

# print warning
for addr, addr_obj in global_mem.items():
    if (len(addr_obj.load) > 1 and len(addr_obj.store) > 1) or \
        (len(addr_obj.load) == 1 and len(addr_obj.store) == 1 and addr_obj.load != addr_obj.store):
        print(bcolors.WARNING + "Warning! There may be a data race in address(Global): " + addr + " where:" + bcolors.ENDC)
        race_counter += 1
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
else:
    print(bcolors.WARNING + "There are {} potential data races in the program".format(race_counter) + bcolors.ENDC)