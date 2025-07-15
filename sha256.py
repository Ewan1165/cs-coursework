from math import ceil
import struct

#Logical right rotate. For example 1000111010 right rotated by 3 would be 0111010100
def RTR(x, n):
    return ((x >> n) | (x << (32-n))) & 0xffffffff

def padBytes(msg):
    length = len(msg) * 8
    msg += b"\x80"
    while (len(msg)*8) % 512 != 448:
        msg += b"\x00"

    msg += struct.pack(">Q", length)

    return msg

def hash(x):
    #Initialise variables
    h0 = 0x6a09e667
    h1 = 0xbb67ae85
    h2 = 0x3c6ef372
    h3 = 0xa54ff53a
    h4 = 0x510e527f
    h5 = 0x9b05688c
    h6 = 0x1f83d9ab
    h7 = 0x5be0cd19

    k = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
       0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
       0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
       0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
       0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
       0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
       0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
       0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]

    #Convert string to bytes
    message = x.encode("utf-8")

    #Pad message out to make its length in bits a multiple of 512
    message = padBytes(message)

    for startPtr in range(0, len(message), 64):
        #Get nth 512 bit chunk
        chunk = message[startPtr: startPtr + 64]
        w = [0] * 64
        #Copy chunk into first 512 bits of array w
        for i in range(16):
            w[i] = struct.unpack(">I", chunk[i*4:i*4+4])[0]

        #Extend the first 16 indexes into the whole array, with each index being made up of the previous words
        for i in range(16,64):
            s0 = RTR(w[i-15], 7) ^ RTR(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = RTR(w[i-2], 17) ^ RTR(w[i-2], 19) ^ (w[i-2] >> 10)
            w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xffffffff

        #Copy in working values
        a,b,c,d,e,f,g,h = h0,h1,h2,h3,h4,h5,h6,h7

        #Main compression loop
        #Mixes the bits in a complex but deterministic way, which causes an avalanche effect
        for i in range(64):
            s1 = RTR(e, 6) ^ RTR(e, 11) ^ RTR(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + s1 + ch + k[i] + w[i]) & 0xffffffff
            s0 = RTR(a, 2) ^ RTR(a, 13) ^ RTR(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xffffffff

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xffffffff

        #Appends the working values to the inital variables
        h0  = (h0 + a) & 0xffffffff
        h1  = (h1 + b) & 0xffffffff
        h2  = (h2 + c) & 0xffffffff
        h3  = (h3 + d) & 0xffffffff
        h4  = (h4 + e) & 0xffffffff
        h5  = (h5 + f) & 0xffffffff
        h6  = (h6 + g) & 0xffffffff
        h7  = (h7 + h) & 0xffffffff

    #Combines the bits of the 8 variables and gets the result in hex
    output = struct.pack(">8L", h0, h1, h2, h3, h4, h5, h6, h7)
    return output.hex()