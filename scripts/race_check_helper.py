#!/usr/bin/env python3
#
# The script will read stdin 
# (which should be output of NVbit tool "race_check_trace").
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

# Thread in a block
class Thread:
    def __init__(self, warp_id, lane_id):
        self.warp_id = warp_id
        self.lane_id = lane_id

    def __hash__(self):
         return hash((self.warp_id, self.lane_id))
    
    def __eq__(self, other):
        return self.warp_id == other.warp_id and \
        self.lane_id == other.lane_id

    def __str__(self):
        return "({} {})".format(self.warp_id, self.lane_id)

# SFR in a block
class SFR:
    def __init__(self, cta_id_x, cta_id_y, cta_id_z, SFR_id):
        self.cta_id_x = cta_id_x
        self.cta_id_y = cta_id_y
        self.cta_id_z = cta_id_z
        self.SFR_id = SFR_id

    def __hash__(self):
         return hash((self.cta_id_x, self.cta_id_y, self.cta_id_z, self.SFR_id))
    
    def __eq__(self, other):
        return self.cta_id_x == other.cta_id_x and \
        self.cta_id_y == other.cta_id_y and \
        self.cta_id_z == other.cta_id_z and \
        self.SFR_id == other.SFR_id

    def __str__(self):
        return "Block_id: ({} {} {}), SFR_id: {}".format(self.cta_id_x, self.cta_id_y, self.cta_id_z, self.SFR_id)


class Block:
    def __init__(self, cta_id_x, cta_id_y, cta_id_z):
        self.cta_id_x = cta_id_x
        self.cta_id_y = cta_id_y
        self.cta_id_z = cta_id_z

    def __hash__(self):
         return hash((self.cta_id_x, self.cta_id_y, self.cta_id_z))
    
    def __eq__(self, other):
        return self.cta_id_x == other.cta_id_x and \
        self.cta_id_y == other.cta_id_y and \
        self.cta_id_z == other.cta_id_z

    def __str__(self):
        return "({} {} {})".format(self.cta_id_x, self.cta_id_y, self.cta_id_z)


SFR_shared_mem = {} # key: SFR, val: shared_mem (a dic of addr : Address)
SFR_global_mem = {} # key: SFR, val: global_mem (a dic of addr : Address)

GLOBAL_mem = {} # key: addr, val: Address (a set of Block)

# read input and build dict
for line in sys.stdin:
    temp = line[4:-1].split(",")
    if (len(temp) != 8):  # skip unwanted output
        continue

    addr = temp[-1]
    t = Thread(temp[4], temp[5])
    s = SFR(temp[1], temp[2], temp[3], temp[-2])
    b = Block(temp[1], temp[2], temp[3])

    if "#ld#" in line: # format: "#ld#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id, SFR_id, addr\n"
        if (temp[0] == '1'): # shared memory
            if s not in SFR_shared_mem:
                SFR_shared_mem[s] = {}

            shared_mem = SFR_shared_mem[s]

            if addr not in shared_mem:
                a = Address()
                a.load.add(t) # add thread id to dict
                shared_mem[addr] = a
            else:
                shared_mem[addr].load.add(t) 

        else: # global memory
            # intra block
            if s not in SFR_global_mem:
                SFR_global_mem[s] = {}

            global_mem = SFR_global_mem[s]

            if addr not in global_mem:
                a = Address()
                a.load.add(t) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].load.add(t)   

            # inter block
            if addr not in GLOBAL_mem:
                a = Address()
                a.load.add(b) # add thread id to dict
                GLOBAL_mem[addr] = a
            else:
                GLOBAL_mem[addr].load.add(b)   


    elif "#st#" in line: # format: "#st#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id, SFR_id, addr\n"
        if (temp[0] == '1'): # shared memory
            if s not in SFR_shared_mem:
                SFR_shared_mem[s] = {}

            shared_mem = SFR_shared_mem[s]

            if addr not in shared_mem:
                a = Address()
                a.store.add(t) # add thread id to dict
                shared_mem[addr] = a
            else:
                shared_mem[addr].store.add(t) 
        else:
            # intra block
            if s not in SFR_global_mem:
                SFR_global_mem[s] = {}

            global_mem = SFR_global_mem[s]

            if addr not in global_mem:
                a = Address()
                a.store.add(t) # add thread id to dict
                global_mem[addr] = a
            else:
                global_mem[addr].store.add(t)    

            # inter block
            if addr not in GLOBAL_mem:
                a = Address()
                a.store.add(b) # add thread id to dict
                GLOBAL_mem[addr] = a
            else:
                GLOBAL_mem[addr].store.add(b)   

race_counter = 0

intra_block_shared_memory_counter = 0
intra_block_global_memory_counter = 0
inter_block_global_memory_counter = 0

# intra block shared memory
for SFR, shared_mem in SFR_shared_mem.items():
    for addr, addr_obj in shared_mem.items():
        if (len(addr_obj.store) > 1) or (len(addr_obj.store) == 1 and \
            (len(addr_obj.load) >= 1 and addr_obj.load != addr_obj.store)) :
            print(bcolors.WARNING + "Warning! There may be a data race in address(SHARED, " + str(SFR) + "): " + addr + " where:" + bcolors.ENDC)
            race_counter += 1
            intra_block_shared_memory_counter += 1
            print("\tLoad from threads: ", end="")
            for l in addr_obj.load:
                print(l, end=" ")

            print("")

            print("\tStore from threads: ", end="")
            for s in addr_obj.store:
                print(s, end=" ")

            print("\n")

# intra block global memory
for SFR, global_mem in SFR_global_mem.items():
    for addr, addr_obj in global_mem.items():
        if (len(addr_obj.store) > 1) or (len(addr_obj.store) == 1 and \
            (len(addr_obj.load) >= 1 and addr_obj.load != addr_obj.store)) :
            print(bcolors.WARNING + "Warning! There may be a data race in address(GLOBAL, " + str(SFR) + "): " + addr + " where:" + bcolors.ENDC)
            race_counter += 1
            intra_block_global_memory_counter += 1
            print("\tLoad from threads: ", end="")
            for l in addr_obj.load:
                print(l, end=" ")

            print("")

            print("\tStore from threads: ", end="")
            for s in addr_obj.store:
                print(s, end=" ")

            print("\n")

# inter block global memory
for addr, addr_obj in GLOBAL_mem.items():
    if (len(addr_obj.store) > 1) or (len(addr_obj.store) == 1 and \
        (len(addr_obj.load) >= 1 and addr_obj.load != addr_obj.store)) :
        print(bcolors.WARNING + "Warning! There may be a data race in address(GLOBAL): " + addr + " where:" + bcolors.ENDC)
        race_counter += 1
        inter_block_global_memory_counter += 1
        print("\tLoad from blocks: ", end="")
        for l in addr_obj.load:
            print(l, end=" ")

        print("")

        print("\tStore from blocks: ", end="")
        for s in addr_obj.store:
            print(s, end=" ")

        print("\n")


if race_counter == 0:
    print(bcolors.OKGREEN + "no data races found."+ bcolors.ENDC)
else:
    print(bcolors.WARNING + "There are {} potential data races in the program".format(race_counter) + bcolors.ENDC)
    print(bcolors.WARNING + "{} of them are intra block shared memory data races in the program".format(intra_block_shared_memory_counter) + bcolors.ENDC)
    print(bcolors.WARNING + "{} of them are intra block global memory data races in the program".format(intra_block_global_memory_counter) + bcolors.ENDC)
    print(bcolors.WARNING + "{} of them are inter block global memory data races in the program".format(inter_block_global_memory_counter) + bcolors.ENDC)