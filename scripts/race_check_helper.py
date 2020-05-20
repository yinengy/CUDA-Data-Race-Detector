#!/usr/bin/env python3
#
# The script will read stdin 
# (which should be output of NVbit tool "race_check_trace").
# And it will grep load and store. 
# Will check if there are conflicting memory accesses (data races)
# A warning will be printed
#
#
# Yineng Yan (yinengy@umich.edu), 2020

import sys

kernel_counter = 0

functions = []

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
        self.load_dic = {}
        self.store_dic = {}

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

class Function:
    def __init__(self, func_name):
        self.func_name = func_name
        self.insts = []


def process_message():
    global functions

    SFR_shared_mem = {} # key: SFR, val: shared_mem (a dic of addr : Address)
    SFR_global_mem = {} # key: SFR, val: global_mem (a dic of addr : Address)

    GLOBAL_mem = {} # key: addr, val: Address (a set of Block)

    # flag and counter for reading function assembly
    read_func = False
    read_func_name = False

    # read input and build dict
    for line in sys.stdin:
        # handle special message (kernel ends signal and function assembly)
        if line.strip('\n') == "#kernelends#":
            check_result(SFR_shared_mem, SFR_global_mem, GLOBAL_mem)
            # do a new loop
            SFR_shared_mem = {} # key: SFR, val: shared_mem (a dic of addr : Address)
            SFR_global_mem = {} # key: SFR, val: global_mem (a dic of addr : Address)

            GLOBAL_mem = {} # key: addr, val: Address (a set of Block)
            continue
        elif line.strip('\n') == "#func_begin#": # begins reading functions
            read_func = True
            continue
        elif line.strip('\n') == "#func_end#": # finish reading functions
            read_func = False
            read_func_name = False
            continue
        elif read_func and (not read_func_name): # if haven't read function name
            functions.append(Function(line.strip('\n')))
            read_func_name = True
            continue
        elif read_func:
            functions[-1].insts.append(line.strip('\n'))
            continue
        
        # handle load and store message
        temp = line.strip('\n')[4:].split(",")

        if (len(temp) != 10):  # skip unwanted output
            continue

        addr = temp[-1]
        t = Thread(temp[4], temp[5])
        s = SFR(temp[1], temp[2], temp[3], temp[-2])
        b = Block(temp[1], temp[2], temp[3])

        if "#ld#" in line: # format: "#ld#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id, func_id, inst_id, SFR_id, addr\n"
            if (temp[0] == '1'): # shared memory
                if s not in SFR_shared_mem:
                    SFR_shared_mem[s] = {}

                shared_mem = SFR_shared_mem[s]

                if addr not in shared_mem:
                    shared_mem[addr] = Address()
                shared_mem[addr].load.add(t) 

            else: # global memory
                # intra block
                if s not in SFR_global_mem:
                    SFR_global_mem[s] = {}

                global_mem = SFR_global_mem[s]

                if addr not in global_mem:
                    a = Address()
                    global_mem[addr] = a

                global_mem[addr].load.add(t)    

                # inter block
                if addr not in GLOBAL_mem:
                    GLOBAL_mem[addr] = Address()

                a = GLOBAL_mem[addr]
                if (b not in a.load_dic):
                    a.load_dic[b] = set()
                a.load_dic[b].add(t) # add thread id to dict


        elif "#st#" in line: # format: "#st#is_shared_memory, cta_id_x, cta_id_y, cta_id_z, warp_id, lane_id,func_id, inst_id, SFR_id, addr\n"
            if (temp[0] == '1'): # shared memory
                if s not in SFR_shared_mem:
                    SFR_shared_mem[s] = {}

                shared_mem = SFR_shared_mem[s]

                if addr not in shared_mem:
                    shared_mem[addr] = Address()
                shared_mem[addr].store.add(t) 
            else:
                # intra block
                if s not in SFR_global_mem:
                    SFR_global_mem[s] = {}

                global_mem = SFR_global_mem[s]

                if addr not in global_mem:
                    a = Address()
                    global_mem[addr] = a

                global_mem[addr].store.add(t)    

                # inter block
                if addr not in GLOBAL_mem:
                    GLOBAL_mem[addr] = Address()

                a = GLOBAL_mem[addr]
                if (b not in a.store_dic):
                    a.store_dic[b] = set()
                a.store_dic[b].add(t) # add thread id to dict

def check_result(SFR_shared_mem, SFR_global_mem, GLOBAL_mem):
    global kernel_counter
    kernel_counter += 1

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
        if (len(addr_obj.store_dic) > 1) or (len(addr_obj.store_dic) == 1 and \
            (len(addr_obj.load_dic) >= 1 and (list(addr_obj.store_dic.keys())[0] not in addr_obj.load_dic))) :
            print(bcolors.WARNING + "Warning! There may be a data race in address(GLOBAL): " + addr + " where:" + bcolors.ENDC)
            race_counter += 1
            inter_block_global_memory_counter += 1
            print("\tLoad from blocks: ", end="")
            for block, thread in addr_obj.load_dic.items():
                print(block, end="-")
                print("[Thread ", end="")
                for t in thread:
                    print(t, end=" ")
                print("]")
                print(" "*23, end="")

            print("\n")

            print("\tStore from blocks: ", end="")
            for block, thread in addr_obj.store_dic.items():
                print(block, end="-")
                print("[Thread ", end="")
                for t in thread:
                    print(t, end=" ")
                print("]")
                print(" "*23, end="")

            print("\n")


    if race_counter == 0:
        print(bcolors.OKGREEN + "no data races found in {}th kernel lunches.".format(kernel_counter) + bcolors.ENDC)
    else:
        print(bcolors.WARNING + "There are {} potential data races in {}th kernel lunches".format(race_counter, kernel_counter) + bcolors.ENDC)
        print(bcolors.WARNING + "{} of them are intra block shared memory data races in this kernel lunches".format(intra_block_shared_memory_counter) + bcolors.ENDC)
        print(bcolors.WARNING + "{} of them are intra block global memory data races in this kernel lunches".format(intra_block_global_memory_counter) + bcolors.ENDC)
        print(bcolors.WARNING + "{} of them are inter block global memory data races in this kernel lunches".format(inter_block_global_memory_counter) + bcolors.ENDC)
        

if __name__ == "__main__":
    process_message()