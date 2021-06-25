#!/usr/bin/python

import numpy as np
import sys

def unpack_8bit_into_12bit(arr_in, out_size):
    
    vals = np.array([0]*out_size, dtype=np.uint16)
    
    bidx = out_size * 12 - 4
    while bidx >= 0:
        
        validx = int(bidx / 12)
        
        arridx = int(bidx / 8)
        
        shift_val = int(bidx % 8)
        vals[validx] |= ((arr_in[arridx] >> shift_val) & 0x0F) << (bidx % 12)

        bidx = bidx - 4

    return vals

def pack_12bit_into_8bit(vals, insize):

    outsize = int( (insize*12) /8)
    arr = np.array([0]*outsize, dtype=np.uint8)

    bidx = insize*12-4
    while bidx >= 0:
    
        validx = int(bidx / 12)
        arridx = int(bidx / 8)
        shift_val = int(bidx % 12)
        arr[arridx] |= ((vals[validx] >> shift_val) & 0x0F) << (bidx % 8)

        bidx = bidx - 4
    
    return arr



def copy_bytearray_to_np_uint16(byte_arr):
    arr = np.array( [0]*len(byte_arr),dtype=np.uint16 )
    idx = 0
    for c in byte_arr:
        arr[idx] = c
        idx = idx+1
    return arr

## Quick example of how to use the 'packing' and 'unpacking' functions below.
## Note that the OUTPUT depends on the system endianness, but that as long as
## they are being used between two systems that have the SAME endianness, they
## will be mutually compatible.

##arr = np.array([1620, 1827, 293, 111, 834, 545], dtype=np.uint16)   #create the original array (must be 0-padded 12 bit)
##print(arr)
##packed = pack_12bit_into_8bit(arr,arr.size) #pack the original array
##for p in packed:
##    print(hex(int(p)))  # kludge-y method to display hexadecimal in python (i don't know python very well)
##unpacked = unpack_8bit_into_12bit(packed,arr.size)  #re-pack the array using the complementary packing function
##print(unpacked) #show our result! it should be the same as the original array

