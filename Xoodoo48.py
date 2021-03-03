# -*- coding: utf-8 -*-

# Preview of the Xoodoo permutation, as presented by Joan Daemen at the ECC
# workshop in Nijmegen, The Netherlands, on November 14th, 2017.

# Implementation by Seth Hoffert, hereby denoted as "the implementer".

# To the extent possible under law, the implementer has waived all copyright
# and related or neighboring rights to the source code in this file.
# http://creativecommons.org/publicdomain/zero/1.0/

# [03/2021] Modified by Anna Guinet to add a variation on a state of 48 bits.

import sys

# Number of bits in lane (len_z) and state (len_s)
len_s, len_z = 48, 4
# len_s, len_z = 384, 32

# Number of rounds (default: 12)
nb_r = 1   

class Xoodoo:
    """
    Define Xoodoo round function.
    """
    rc_s = []
    rc_p = []

    def __init__(self):
        s = 1
        p = 1

        for i in range(6):
            self.rc_s.append(s)
            s = (s * 5) % 7

        for i in range(7):
            self.rc_p.append(p)
            p = p ^ (p << 2)
            if (p & 0b10000) != 0: p ^= 0b10110
            if (p & 0b01000) != 0: p ^= 0b01011

    def Permute(self, A, r):
        for i in range(1 - r, 1):
            A = self.__Round(A, i)

        return A

    def __Round(self, A, i):

        # θ
        P = A[0] ^ A[1] ^ A[2]
        E = CyclicShiftPlane(P, 1, 5) ^ CyclicShiftPlane(P, 1, 14)
        for y in range(3): A[y] = A[y] ^ E

        # ρ_west
        A[1] = CyclicShiftPlane(A[1], 1, 0)
        A[2] = CyclicShiftPlane(A[2], 0, 11)

        # ι
        rc = int()
        if len_s == 48:
            rc = 0b0010  # truncate round constant for i = 0
        if len_s > 48:
            rc = (self.rc_p[-i % 7] ^ 0b1000) << self.rc_s[-i % 6]
        A[0][0] = A[0][0] ^ rc

        # χ
        B = State()
        B[0] = ~A[1] & A[2]
        B[1] = ~A[2] & A[0]
        B[2] = ~A[0] & A[1]
        for y in range(3): A[y] = A[y] ^ B[y]

        # ρ_east
        A[1] = CyclicShiftPlane(A[1], 0, 1)
        A[2] = CyclicShiftPlane(A[2], 2, 8)

        return A

def not_lane(b, n):
    """
    Bitwise NOT in Python for n bits by default. 
    """
    return (1 << n) - 1 - b

def ReduceX(x):
    return ((x % 4) + 4) % 4

def ReduceZ(z):
    return ((z % len_z) + len_z) % len_z

def CyclicShiftLane(a, dz):
    dz = ReduceZ(dz)

    if dz == 0:
        return a
    else:
        return ((a >> (len_z - (dz % len_z))) | (a << (dz % len_z))) % (1 << len_z)

class Plane:
    """
    Define Xoodoo plane of 4 lanes.
    """
    lanes = []

    def __init__(self, lanes = None):
        if lanes is None:
            lanes = [0] * 4
        self.lanes = lanes

    def __getitem__(self, i):
        return self.lanes[i]

    def __setitem__(self, i, v):
        self.lanes[i] = v

    def __str__(self):
        if len_s == 48:
            return ' '.join("0b{:04b}".format(x) for x in self.lanes)  # 4 bits
        if len_s > 48:
            return ' '.join("0x{:08x}".format(x) for x in self.lanes)  # byte

    def __xor__(self, other):
        return Plane([self.lanes[x] ^ other.lanes[x] for x in range(4)])

    def __and__(self, other):
        return Plane([self.lanes[x] & other.lanes[x] for x in range(4)])

    def __invert__(self):
        """ bitwise NOT """
        return Plane([not_lane(self.lanes[x], len_z) for x in range(4)]) 

def CyclicShiftPlane(A, dx, dz):
    p = Plane()

    for i in range(4):
        index = ReduceX(i - dx)
        p[i] = CyclicShiftLane(A[index], dz)

    return p

def load32(byte):
    """
    bytearray to int (little endianness)
    """
    return sum((byte[i] << (8 * i)) for i in range(4))

def load4(b):
    """ 
    Convert 4-bit binary in integer.
    """
    return int(b, 2)

def format_state(byte, n):
    """ 
    Display 6 bytes in n bits with leading zeros.
    """
    data = int.from_bytes(byte, byteorder=sys.byteorder)
    out  = format(data, '0%sb' % n)
    return out

class State:
    """
    Define 48-bit Xoodoo state.
    """
    planes = []

    def __init__(self, state = None):
        if state is None:
            state = bytearray(len_s // 8)

        if len_s == 48:  # 4 bits
            state = format_state(state, len_s)
            self.planes = [Plane([load4(state[4*(x+4*y):4*(x+4*y)+4]) for x in range(4)]) for y in range(3)]
        
        if len_s > 48:   # bytes
            self.planes = [Plane([load32(state[4*(x+4*y):4*(x+4*y)+4]) for x in range(4)]) for y in range(3)]

    def __getitem__(self, i):
        return self.planes[i]

    def __setitem__(self, i, v):
        self.planes[i] = v

    def __str__(self):
        return ' '.join(str(x) for x in self.planes)

xp = Xoodoo()
# A  = State()


###########################################################

print('\n----- Message\n')

m = 0xcc45e92666d8
print('hex :', hex(m))

M = State(bytearray(b'\xcc\x45\xe9\x26\x66\xd8')) 
print('Plane 2: ', M.planes[2])
print('Plane 1: ', M.planes[1])
print('Plane 0: ', M.planes[0])
 

print('\n----- Key\n')

k = 0x52a78352c6a9
print('hex :', hex(k))

K = State(bytearray(b'\x52\xa7\x83\x52\xc6\xa9')) 
print('Plane 2: ', K.planes[2])
print('Plane 1: ', K.planes[1])
print('Plane 0: ', K.planes[0])
print()


print('\n--------- Before round ---------\n')
km = hex(k ^ m)  # 0x9ee26a74a071
print('hex : ', km)

A = State(bytearray(b'\x9e\xe2\x6a\x74\xa0\x71'))

print('Plane 2: ', A.planes[2])
print('Plane 1: ', A.planes[1])
print('Plane 0: ', A.planes[0])

###########################################################

for i in range(len_s): A = xp.Permute(A, nb_r)

print('\n--------- After round  ---------\n')
print('Plane 0: ', A.planes[2])
print('Plane 1: ', A.planes[1])
print('Plane 2: ', A.planes[0])
print(A)
print()
